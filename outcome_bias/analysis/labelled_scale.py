"""X1, the labelled-scale test: E3's violation question asked with a labelled scale, with and without an
instruction to set aside what happened afterwards (plans: docs/1_main_experiments/plan.md, docs/2_follow_ups/plan.md B).

  python -m outcome_bias.analysis.labelled_scale

For each model, on the 21 borderline scenarios: mean score per ending, harm minus payoff, harm minus
no ending, payoff minus no ending, and the change in harm minus payoff from E3's first run (paired by
scenario). E3's own re-run is shown as a yardstick for run-to-run noise.
"""

from outcome_bias import runlog
from outcome_bias.analysis.load import answers, select
from outcome_bias.stats import change, cond_mean, contrast, fmt, unit_means

ARMS = [  # (name, run label)
    ("E3, original question, run 1", "run1"),
    ("E3, original question, re-run", "run2"),
    ("Labelled scale", "x1-labelled"),
    ("Labelled scale + instruction", "x1-ignore"),
    ("Labelled scale + instruction, re-run (rule 2)", "x1-ignore-run2"),
]


def violation_means(label, model):
    rows, bad = answers(label, "e3", model)
    if rows is None:
        return None, 0
    return unit_means(select(rows, "violation", "borderline")), bad


def main():
    for model in runlog.judged(exp="e3"):
        print(f"\n===== {model}  (violation question, 21 borderline scenarios)")
        base, _ = violation_means("run1", model)
        for name, label in ARMS:
            um, bad = violation_means(label, model)
            if um is None:
                continue
            means = "  ".join(f"{c} {cond_mean(um, c):5.1f}" for c in ("payoff", "omitted", "harm"))
            print(f"\n  {name}  ({bad} unparsed)   {means}")
            for a, b in (("harm", "payoff"), ("harm", "omitted"), ("payoff", "omitted")):
                print(f"      {a + ' - ' + b:<18} {fmt(contrast(um, a, b))}")
            if label != "run1":
                print(f"      change in harm - payoff from E3 run 1:  {fmt(change(um, base, 'harm', 'payoff'))}")
    print("\n* = 95% interval excludes zero.")


if __name__ == "__main__":
    main()
