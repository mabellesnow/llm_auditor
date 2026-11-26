"""The open-weight check (docs/5_open_models/results.md): Figure 2's test on Inkling 2 Mini beside Claude and Gemini.

  python -m outcome_bias.analysis.open_comparison

E3's borderline transcripts, first runs, the three questions Inkling was run on. Each cell is the scenario-paired
change between two endings with its bootstrap 95% interval; * marks an interval that excludes zero. Inkling has
one run and no written plan, so its cells describe; they don't claim effects under the main plan's rules.
"""

from outcome_bias.analysis.load import answers, select
from outcome_bias.models import CLAUDE, GEMINI, OPEN, SHORT_NAMES
from outcome_bias.stats import cond_mean, contrast, fmt_full, fmt_short, unit_means
from outcome_bias.verify import check_freeze

MODELS = CLAUDE + GEMINI + OPEN
QUESTIONS = ("violation", "blame", "risk")
TESTS = [(q, a, b) for q in QUESTIONS for a, b in (("payoff", "omitted"), ("harm", "omitted"), ("harm", "payoff"))]
NAME = {"payoff": "payoff", "harm": "harm", "omitted": "no ending"}


def main():
    check_freeze()
    rows = {m: answers("run1", "e3", m) for m in MODELS}
    print("\n## Change between endings  (E3 borderline, first runs; * = 95% interval excludes zero)\n")
    print("| Question | Contrast | " + " | ".join(SHORT_NAMES[m] for m in MODELS) + " |")
    print("|---|---|" + "---|" * len(MODELS))
    for q, a, b in TESTS:
        cs = [contrast(unit_means(select(rows[m][0], q, "borderline")), a, b) for m in MODELS]
        print(f"| {q} | {NAME[a]} − {NAME[b]} | " + " | ".join(fmt_short(c, 1) for c in cs) + " |")
    print("\n## Inkling in detail\n")
    for q, a, b in TESTS:
        c = contrast(unit_means(select(rows["inkling-2-mini"][0], q, "borderline")), a, b)
        print(f"- {q}, {NAME[a]} − {NAME[b]}: {fmt_full(c, 1, star=True)}"
              + (f"  ({c[3]} scenarios up, {c[4]} down, of {c[5]})" if c else ""))
    print("\n## Mean with no ending  (E3 borderline, 0–100)\n")
    print("| Question | " + " | ".join(SHORT_NAMES[m] for m in MODELS) + " |")
    print("|---|" + "---|" * len(MODELS))
    for q in QUESTIONS:
        means = [cond_mean(unit_means(select(rows[m][0], q, "borderline")), "omitted") for m in MODELS]
        print(f"| {q} | " + " | ".join(f"{x:.1f}" for x in means) + " |")
    print("\nUnparsed answers: " + ", ".join(f"{SHORT_NAMES[m]} {rows[m][1]}" for m in MODELS))


if __name__ == "__main__":
    main()
