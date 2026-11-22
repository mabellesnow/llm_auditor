"""The pre-registered analysis of E1 to E5 (plan: docs/1_main_experiments/plan.md).

  python -m outcome_bias.analysis.main_experiments e3                      # first run, main arm, all models
  python -m outcome_bias.analysis.main_experiments e3 --label run2         # the rule 2 re-run
  python -m outcome_bias.analysis.main_experiments e2 --arm reasoning      # the reasoning-on arm
  python -m outcome_bias.analysis.main_experiments --logs logs/a.eval ...  # any logs of one experiment

For each model, version and question: the mean per ending, and the pre-registered contrasts with
bootstrap 95% intervals over units. Runs of the same model and reasoning setting are pooled.
"""

import argparse
import statistics as st
import sys
from collections import defaultdict

from outcome_bias import runlog
from outcome_bias.analysis.load import load
from outcome_bias.models import rank
from outcome_bias.stats import boot, contrast, digits_for, fmt, unit_means
from outcome_bias.verify import check_freeze

# Primary contrast first in each list (worse ending minus better ending).
CONTRASTS = {
    "e1": [("bad", "good"), ("bad", "none"), ("good", "none")],
    "e2": [("failure", "success"), ("success", "omitted"), ("failure", "omitted")],
    "e3": [("harm", "payoff"), ("payoff", "omitted"), ("harm", "omitted")],
    "e4": [("failure", "success"), ("success", "none"), ("failure", "none")],
    "e5": [("harm", "noharm"), ("harm", "none"), ("noharm", "none")],
}
COND_ORDER = {
    "e1": ("good", "none", "bad"), "e2": ("success", "omitted", "failure"), "e3": ("payoff", "omitted", "harm"),
    "e4": ("success", "none", "failure"), "e5": ("noharm", "none", "harm"),
}


def performance_did(R):
    """E2: the cost of the shortcut on the performance score (compliant minus borderline), after success
    minus after failure. The predicted bias makes it negative."""
    cells = defaultdict(list)
    for r in R:
        if r["question"] == "performance" and r["version"] in ("borderline", "compliant"):
            cells[(r["unit"], r["version"], r["cond"])].append(r["answer"])
    units = sorted({k[0] for k in cells if k[1] == "borderline"})
    units = [u for u in units if all(cells.get((u, v, c)) for v in ("borderline", "compliant")
                                     for c in ("success", "failure", "omitted"))]  # a cell can be empty if unparsed
    cost = {c: [st.mean(cells[(u, "compliant", c)]) - st.mean(cells[(u, "borderline", c)]) for u in units]
            for c in ("success", "failure", "omitted")}
    did = boot([s - f for s, f in zip(cost["success"], cost["failure"])])
    return cost, did


def report(rows):
    exp = rows[0]["exp"]
    groups = sorted({(r["model"], r["reasoning"]) for r in rows}, key=lambda g: (rank(g[0]), g[1]))
    for model, reasoning in groups:
        R = [r for r in rows if r["model"] == model and r["reasoning"] == reasoning]
        thought = st.mean(r["thought"] for r in R)
        print(f"\n===== {exp.upper()}  {model}  reasoning={reasoning}  "
              f"({len(R)} answers; reasoning tokens used in {thought:.0%})")
        versions = (["all"] if exp == "e1" else []) + sorted({r["version"] for r in R})
        for version in versions:
            V = R if version == "all" else [r for r in R if r["version"] == version]
            value, questions = ("detected", ["detect"]) if exp == "e4" else \
                ("answer", list(dict.fromkeys(r["question"] for r in V)))
            print(f"\n  -- {version} ({len({r['unit'] for r in V})} units)")
            for q in questions:
                um = unit_means([r for r in V if r["question"] == q], value)
                d = 2 if exp == "e4" else digits_for(q)
                means = "  ".join(f"{c} {st.mean(v for (u, cc), v in um.items() if cc == c):.{d}f}"
                                  for c in COND_ORDER[exp] if any(cc == c for _, cc in um))
                print(f"  {'listed target' if exp == 'e4' else q:<13} {means}")
                for a, b in CONTRASTS[exp]:
                    c = contrast(um, a, b)
                    if c:
                        print(f"      {a + ' - ' + b:<20} {fmt(c, d, counts=True)}")
            if exp == "e4":
                um = unit_means(V, "others")
                print("  other tickets listed per session: " + "  ".join(
                    f"{c} {st.mean(v for (u, cc), v in um.items() if cc == c):.2f}" for c in COND_ORDER[exp]))
        if exp == "e2":
            cost, did = performance_did(R)
            print("\n  -- performance score: cost of the shortcut (compliant minus borderline), by ending")
            print("  " + "  ".join(f"{c} {st.mean(v):.2f}" for c, v in cost.items()))
            print(f"      cost after success - cost after failure   {fmt(did, 2)}"
                  "   (negative = the shortcut costs less when the task succeeded)")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("exp", nargs="?", choices=sorted(CONTRASTS))
    p.add_argument("--label", default="run1")
    p.add_argument("--arm", default="main")
    p.add_argument("--logs", nargs="+", help="analyse these log files instead of looking them up")
    a = p.parse_args(argv)
    paths = a.logs or (runlog.logs(label=a.label, exp=a.exp, arm=a.arm) if a.exp else None)
    if not paths:
        sys.exit("No logs found. Give an experiment (and --label / --arm) or --logs.")
    check_freeze()
    rows, bad = load(paths)
    print(f"{len(rows)} parsed answers, {bad} unparsed or errored.")
    for exp in sorted({r["exp"] for r in rows}):
        report([r for r in rows if r["exp"] == exp])
    print("\n* = 95% interval excludes zero. Per the pre-registration, an effect is claimed only when this holds "
          "in the same direction for at least two of the three models.")


if __name__ == "__main__":
    main()
