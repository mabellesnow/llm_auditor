"""Follow-ups, parts A to D (plan: docs/2_follow_ups/plan.md, where they are called stage 2).

  python -m outcome_bias.analysis.follow_ups

  A  Opus re-runs of E2 and E3: each effect claimed for Opus, first run against re-run
  B  the instruction to ignore what happened afterwards (details: python -m outcome_bias.analysis.labelled_scale)
  C  E5 with a neutral note: each ending against the neutral note and against no ending
  D  E3 with each rule's purpose stated: harm minus payoff, and its change from E3's first run
"""

from outcome_bias import runlog
from outcome_bias.analysis.load import answers, select
from outcome_bias.stats import change, contrast, digits_for, direction, fmt, unit_means
from outcome_bias.verify import check_freeze

# Part A: (exp, version, question, a, b, direction claimed in the first run)
OPUS_CLAIMS = [
    ("e2", "borderline", "risk", "failure", "success", +1),
    ("e2", "compliant", "quality", "failure", "success", -1),
    ("e2", "compliant", "risk", "failure", "success", +1),
    ("e2", "compliant", "performance", "failure", "success", -1),
    ("e3", "borderline", "blame", "harm", "payoff", +1),
    ("e3", "borderline", "sanction", "harm", "payoff", +1),
    ("e3", "borderline", "accept", "harm", "payoff", -1),
    ("e3", "borderline", "quality", "harm", "payoff", -1),
    ("e3", "borderline", "performance", "harm", "payoff", -1),
    ("e3", "borderline", "risk", "harm", "payoff", +1),
]


def _contrast(rows, q, version, a, b):
    return contrast(unit_means(select(rows, q, version)), a, b) if rows else None


def part_a():
    print("\n=== A. Opus re-runs (rule 2): first run, then re-run")
    runs = {(exp, label): answers(label, exp, "opus")[0] for exp in ("e2", "e3") for label in ("run1", "run2")}
    for exp, version, q, a, b, sign in OPUS_CLAIMS:
        c1 = _contrast(runs[(exp, "run1")], q, version, a, b)
        c2 = _contrast(runs[(exp, "run2")], q, version, a, b)
        verdict = "not run yet" if not c2 else ("confirmed" if direction(c2) == sign else "NOT confirmed")
        d = digits_for(q)
        print(f"  {exp} {version:<10} {q:<11} {a}-{b:<8} {fmt(c1, d):<26} {fmt(c2, d):<26} {verdict}")


def part_b():
    print("\n=== B. Instruction to ignore what happened afterwards: change in harm - payoff (violation) from E3 run 1")
    for model in runlog.judged():
        base = answers("run1", "e3", model)[0]
        cells = []
        for label in ("x1-labelled", "x1-ignore", "x1-ignore-run2"):
            rows = answers(label, "e3", model)[0]
            c = change(unit_means(select(rows, "violation", "borderline")),
                       unit_means(select(base, "violation", "borderline")), "harm", "payoff") if rows else None
            cells.append(f"{label} {fmt(c)}")
        print(f"  {model:<7} " + "   ".join(cells))


def part_c():
    print("\n=== C. E5 with a neutral note")
    pairs = [("noharm", "neutral"), ("harm", "neutral"), ("neutral", "none"), ("harm", "noharm"), ("noharm", "none")]
    for label in ("s2-e5_neutral", "s2-e5_neutral-run2"):
        print(f"\n  -- {label}")
        for model in runlog.judged():
            rows, bad = answers(label, "e5", model)
            if rows is None:
                print(f"  {model}: not run yet")
                continue
            print(f"  {model}  ({len(rows)} answers, {bad} unparsed)")
            for q in ("intent", "suspicion", "action"):
                um = unit_means(select(rows, q))
                print(f"    {q:<10} " + "   ".join(f"{a}-{b} {fmt(contrast(um, a, b), digits_for(q))}" for a, b in pairs))


def part_d():
    print("\n=== D. E3 with each rule's purpose stated, borderline versions")
    for label in ("s2-purpose", "s2-purpose-run2"):
        print(f"\n  -- {label}")
        for model in runlog.judged():
            rows, bad = answers(label, "e3", model)
            if rows is None:
                print(f"  {model}: not run yet")
                continue
            base = answers("run1", "e3", model)[0]
            rerun = answers("run2", "e3", model)[0]
            print(f"  {model}  ({len(rows)} answers, {bad} unparsed)")
            for q in ("violation", "quality", "blame", "risk"):
                um, um0 = unit_means(select(rows, q, "borderline")), unit_means(select(base, q, "borderline"))
                hp, hp0 = contrast(um, "harm", "payoff"), contrast(um0, "harm", "payoff")
                share = f"{hp[0] / hp0[0]:.0%} of E3" if hp and hp0 and hp0[0] else ""
                print(f"    {q:<10} harm-payoff {fmt(hp)} ({share})   change from E3 run 1 {fmt(change(um, um0, 'harm', 'payoff'))}"
                      + (f"   E3 re-run vs run 1 (noise) {fmt(change(unit_means(select(rerun, q, 'borderline')), um0, 'harm', 'payoff'))}"
                         if rerun else ""))


def main():
    check_freeze()
    part_a()
    part_b()
    part_c()
    part_d()
    print("\n* = 95% interval excludes zero (bootstrap over scenarios).")


if __name__ == "__main__":
    main()
