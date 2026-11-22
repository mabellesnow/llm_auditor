"""Moderator analysis (exploratory): which kinds of rule are most outcome-sensitive in E3?
Results: docs/3_extra_analyses/results.md.

  python -m outcome_bias.analysis.moderators          # writes docs/3_extra_analyses/tables/moderators_*.csv
  python -m outcome_bias.analysis.moderators --family gemini   # the Gemini models, to moderators_*_gemini.csv

Per scenario and model (E3 borderline, first run and re-run pooled): the harm-minus-payoff effect on
each question, and the no-ending violation score (how much room the verdict had to move).
Scenarios are coded in outcome_bias/analysis/scenario_codes.yaml by rule type (approval, threshold, timing, data,
other) and by who bears the harm (money, people). With 21 scenarios and 2 to 7 per category, this can
show large differences only; tests are permutation tests that shuffle codes across scenarios.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from outcome_bias.analysis.load import frame
from outcome_bias.models import CLAUDE, FAMILIES, ORDER
from outcome_bias.paths import EXTRA_TABLES
from outcome_bias.stats import boot

OUT = EXTRA_TABLES
CODES = Path(__file__).with_name("scenario_codes.yaml")  # analyst codes for each scenario
QUESTIONS = ("violation", "blame", "accept", "quality", "risk")


def codes():
    return pd.DataFrame(yaml.safe_load(CODES.read_text())).set_index("id")


def scenario_effects(models=CLAUDE):
    """One row per (model, scenario, question): harm - payoff, harm - none, and the no-ending violation score."""
    df = frame("e3", models=models)
    if df.empty:
        raise SystemExit(f"No E3 runs for {', '.join(models)} yet")
    df = df[df.version == "borderline"]
    cell = df.groupby(["model", "unit", "question", "cond"]).answer.mean().unstack("cond")
    eff = pd.DataFrame({"harm_payoff": cell["harm"] - cell["payoff"], "harm_none": cell["harm"] - cell["omitted"],
                        "payoff_none": cell["payoff"] - cell["omitted"]}).reset_index()
    base = cell.xs("violation", level="question")["omitted"].rename("baseline_violation").reset_index()
    eff = eff.merge(base, on=["model", "unit"]).merge(codes(), left_on="unit", right_index=True)
    return eff


def by_category(eff, column, question, model=None):
    sel = eff[(eff.question == question) & ((eff.model == model) if model else True)]
    # pool models by averaging within scenario first, so each scenario counts once
    per = sel.groupby(["unit", column]).harm_payoff.mean().reset_index()
    out = []
    for cat, g in per.groupby(column):
        vals = list(g.harm_payoff)
        m, lo, hi = boot(vals) if len(vals) > 1 else (vals[0], np.nan, np.nan)
        out.append(dict(question=question, model=model or "all", code=column, category=cat, n=len(vals), mean=m, lo=lo, hi=hi))
    return out


def permutation_p(eff, column, question, n=5000, seed=0):
    """Between-category spread of scenario means against shuffled codes (models averaged within scenario)."""
    per = eff[eff.question == question].groupby(["unit", column]).harm_payoff.mean().reset_index()
    vals, labels = per.harm_payoff.to_numpy(), per[column].to_numpy()

    def spread(lab):
        means = [vals[lab == c].mean() for c in np.unique(lab)]
        sizes = [np.sum(lab == c) for c in np.unique(lab)]
        grand = vals.mean()
        return sum(s * (m - grand) ** 2 for s, m in zip(sizes, means))

    observed = spread(labels)
    rng = np.random.default_rng(seed)
    null = [spread(rng.permutation(labels)) for _ in range(n)]
    return observed, float(np.mean([x >= observed for x in null]))


def ceiling(eff):
    """Correlation, across scenarios, between the no-ending violation score and the harm effect on the verdict."""
    out = []
    v = eff[eff.question == "violation"]
    for model in judged(eff):
        g = v[v.model == model]
        out.append(dict(model=model, r_harm_payoff=np.corrcoef(g.baseline_violation, g.harm_payoff)[0, 1],
                        r_harm_none=np.corrcoef(g.baseline_violation, g.harm_none)[0, 1]))
    return out


def judged(eff):
    return tuple(m for m in ORDER if m in set(eff.model))


def run(family="claude"):
    eff = scenario_effects(FAMILIES[family])
    sfx = "" if family == "claude" else f"_{family}"
    OUT.mkdir(parents=True, exist_ok=True)
    eff.to_csv(OUT / f"moderators_scenario_effects{sfx}.csv", index=False, float_format="%.3f")
    rows, tests = [], []
    for column in ("rule_type", "harm_domain"):
        for q in QUESTIONS:
            rows += by_category(eff, column, q)
            for model in judged(eff):
                rows += by_category(eff, column, q, model)
            stat, p = permutation_p(eff, column, q)
            tests.append(dict(code=column, question=q, spread=stat, p_permutation=p))
    cats = pd.DataFrame(rows)
    cats.to_csv(OUT / f"moderators_by_category{sfx}.csv", index=False, float_format="%.3f")
    tests = pd.DataFrame(tests)
    tests.to_csv(OUT / f"moderators_tests{sfx}.csv", index=False, float_format="%.4f")
    ceil = pd.DataFrame(ceiling(eff))
    ceil.to_csv(OUT / f"moderators_ceiling{sfx}.csv", index=False, float_format="%.3f")

    pd.set_option("display.width", 200)
    for column in ("rule_type", "harm_domain"):
        print(f"\n=== harm - payoff by {column} (scenario means, models averaged; per-model in the CSV)")
        t = cats[(cats.code == column) & (cats.model == "all")]
        print(t.pivot(index="category", columns="question", values="mean").round(1).to_string())
        print("n scenarios:", t.groupby("category").n.first().to_dict())
        print(tests[tests.code == column][["question", "p_permutation"]].to_string(index=False))
    print("\n=== room to move: correlation of no-ending violation score with the harm effect on the verdict")
    print(ceil.round(2).to_string(index=False))
    print("\n=== per scenario, violation, harm - payoff (models averaged)")
    v = eff[eff.question == "violation"].groupby(["unit", "rule_type", "harm_domain"]).agg(
        harm_payoff=("harm_payoff", "mean"), baseline=("baseline_violation", "mean")).sort_values("harm_payoff")
    print(v.round(1).to_string())
    return eff, cats, tests, ceil


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--family", default="claude", choices=sorted(FAMILIES))
    run(p.parse_args().family)
