"""Mixed-effects models and standardised effect sizes for the main contrasts (exploratory, not
pre-registered). Results: docs/3_extra_analyses/results.md.

  python -m outcome_bias.analysis.mixed_models          # writes docs/3_extra_analyses/tables/mixed_models.csv
  python -m outcome_bias.analysis.mixed_models --family gemini   # the Gemini models, to mixed_models_gemini.csv

For each contrast (ending a vs ending b) and question, on every answer from the first run and the re-run:

  pooled     answer ~ x, with crossed random effects: scenario (intercept and slope), model (intercept and
             slope), scenario-by-model (intercept and slope) and wording (where an ending has two wordings).
             x = +0.5 for ending a, -0.5 for ending b, so the coefficient is a minus b.
             Model is a random effect with only three levels, so its variance is poorly estimated and the
             pooled interval is wide. Read the pooled row as "the average effect across these models".
  per model  answer ~ x, random intercept and slope by scenario, plus wording.

Effect sizes:
  d_lmm  coefficient / SD of a single answer implied by the model (all variance components plus the
         residual; slopes weighted by 0.25 under the +-0.5 coding). Westfall, Kenny and Judd (2014).
  d_av   mean difference / pooled SD of individual answers in the two conditions. Closest to the
         between-subjects effect sizes reported in human studies.
  d_z    mean of per-scenario differences / their SD (the paired design used in the pre-registered analysis).
"""

import argparse
import warnings

import numpy as np
import pandas as pd
from statsmodels.regression.mixed_linear_model import MixedLM

from outcome_bias.analysis.load import frame
from outcome_bias.models import FAMILIES
from outcome_bias.paths import extra_table

# (name, exp, run labels, version, a, b, questions)
CONTRASTS = [
    ("E1 people", "e1", ("run1", "run2"), None, "bad", "good", ("blame", "punish", "wrong", "risk", "quality")),
    ("E2 borderline", "e2", ("run1", "run2"), "borderline", "failure", "success",
     ("violation", "quality", "blame", "sanction", "accept", "performance", "risk")),
    ("E2 compliant", "e2", ("run1", "run2"), "compliant", "failure", "success", ("quality", "risk", "performance")),
    ("E3 borderline", "e3", ("run1", "run2"), "borderline", "harm", "payoff",
     ("violation", "quality", "blame", "sanction", "accept", "performance", "risk")),
    ("E5", "e5", ("run1", "run2"), None, "harm", "noharm", ("intent", "suspicion", "action")),
    ("Stage 2 C", "e5", ("s2-e5_neutral", "s2-e5_neutral-run2"), None, "noharm", "neutral", ("intent", "suspicion")),
]


def _prepare(df, a, b):
    d = df[df.cond.isin([a, b])].copy()
    d["x"] = np.where(d.cond == a, 0.5, -0.5)
    d["g"] = 1
    d["cellw"] = d.unit + "|" + d.cond + "|" + d.wording.astype(str)
    d["um"] = d.unit + "|" + d.model
    return d


def _fit(model):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = model.fit(reml=True, method=["lbfgs"])
    converged = bool(getattr(r, "converged", True)) and not any("converge" in str(x.message).lower() for x in w)
    return r, converged


def _effect_sizes(d, a, b):
    xa, xb = d[d.cond == a].answer, d[d.cond == b].answer
    d_av = (xa.mean() - xb.mean()) / np.sqrt((xa.var() + xb.var()) / 2)
    per = d.groupby(["model", "unit", "cond"]).answer.mean().unstack("cond").dropna()
    diffs = per[a] - per[b]
    d_z = diffs.mean() / diffs.std() if diffs.std() > 0 else np.nan
    return d_av, d_z


def fit_pooled(d, wordings):
    vc = {"scenario": "0 + C(unit)", "scenario_slope": "0 + C(unit):x", "model": "0 + C(model)",
          "model_slope": "0 + C(model):x", "scen_model": "0 + C(um)", "scen_model_slope": "0 + C(um):x"}
    if wordings:
        vc["wording"] = "0 + C(cellw)"
    r, ok = _fit(MixedLM.from_formula("answer ~ x", groups="g", re_formula="0", vc_formula=vc, data=d))
    comps = dict(zip(r.model.exog_vc.names, r.vcomp, strict=True))
    total = sum(v * (0.25 if name.endswith("slope") else 1) for name, v in comps.items()) + r.scale
    return r, ok, comps, total


def fit_one_model(d, wordings):
    vc = {"wording": "0 + C(cellw)"} if wordings else None
    r, ok = _fit(MixedLM.from_formula("answer ~ x", groups="unit", re_formula="~x", vc_formula=vc, data=d))
    cov = np.diag(r.cov_re.values)
    comps = {"scenario": cov[0], "scenario_slope": cov[1]}
    if wordings:
        comps["wording"] = r.vcomp[0]
    total = comps["scenario"] + 0.25 * comps["scenario_slope"] + comps.get("wording", 0) + r.scale
    return r, ok, comps, total


def run(family="claude"):
    models = FAMILIES[family]
    rows = []
    for name, exp, labels, version, a, b, questions in CONTRASTS:
        df = frame(exp, labels, models=models)
        if df.empty:
            continue
        present = tuple(m for m in models if m in set(df.model))
        who_all = (("pooled",) if len(present) > 1 else ()) + present
        if version:
            df = df[df.version == version]
        for q in questions:
            d = _prepare(df[df.question == q], a, b)
            wordings = d.wording.nunique() > 1
            for who in who_all:
                dd = d if who == "pooled" else d[d.model == who]
                r, ok, comps, total = (fit_pooled if who == "pooled" else fit_one_model)(dd, wordings)
                beta = r.fe_params["x"]
                lo, hi = r.conf_int().loc["x"].values
                d_av, d_z = _effect_sizes(dd, a, b)
                rows.append(dict(contrast=name, question=q, a=a, b=b, model=who, n=len(dd), beta=beta, lo=lo, hi=hi,
                                 d_lmm=beta / np.sqrt(total), d_av=d_av, d_z=d_z, converged=ok,
                                 **{f"var_{k}": v for k, v in comps.items()}, var_residual=r.scale))
                print(f"{name:<14} {q:<11} {who:<7} beta {beta:+7.2f} [{lo:+7.2f}, {hi:+7.2f}]  d_lmm {beta / np.sqrt(total):+.2f}"
                      f"  d_av {d_av:+.2f}  d_z {d_z:+.2f}{'' if ok else '  (not converged)'}", flush=True)
    out = pd.DataFrame(rows)
    path = extra_table("mixed_models", family)
    out.to_csv(path, index=False, float_format="%.4f")
    print(f"\nwrote {path}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--family", default="claude", choices=sorted(FAMILIES))
    run(p.parse_args().family)
