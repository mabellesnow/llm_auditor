"""The Gemini comparison (plan: docs/4_gemini/plan.md).

  python -m outcome_bias.analysis.gemini_comparison

For each test of hypotheses G1 to G8: Claude's first run beside each Gemini model's first run and re-run.
Rules as in the main plan, applied within the Gemini family:
  claimed    the first-run interval excludes zero in the predicted direction in at least two of the three
             Gemini models (rule 1). For a test with no predicted direction, in the same direction.
  confirmed  for each model the effect was claimed on, its re-run's interval excludes zero the same way (rule 2).
"""

from outcome_bias.analysis.load import answers, select
from outcome_bias.models import CLAUDE, GEMINI, SHORT_NAMES
from outcome_bias.stats import change, contrast, digits_for, direction, fmt_full, fmt_short, unit_means
from outcome_bias.verify import check_freeze

# (hypothesis, contrast, exp, (first-run label, re-run label or None), arm, version, question, a, b,
#  predicted sign (+1, -1, or 0 for none), change from E3's first run?)
TESTS = [
    ("E1", "Human stories: blame, bad − good", "e1", ("run1", "run2"), "main", None, "blame", "bad", "good", +1, False),
    ("E1", "Human stories: blame, good − no ending", "e1", ("run1", "run2"), "main", None, "blame", "good", "none", 0, False),
    ("G1", "E3: violation, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "violation", "harm", "payoff", +1, False),
    ("G1", "E3: violation, harm − no ending", "e3", ("run1", "run2"), "main", "borderline", "violation", "harm", "omitted", +1, False),
    ("G1", "E3: blame, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "blame", "harm", "payoff", +1, False),
    ("G1", "E3: sanction, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "sanction", "harm", "payoff", +1, False),
    ("G1", "E3: accept as it stands, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "accept", "harm", "payoff", -1, False),
    ("G2", "E3: violation, payoff − no ending", "e3", ("run1", "run2"), "main", "borderline", "violation", "payoff", "omitted", 0, False),
    ("G3", "E1: risk at the time, bad − good", "e1", ("run1", "run2"), "main", None, "risk", "bad", "good", +1, False),
    ("G3", "E2 compliant agent: risk at the time, failure − success", "e2", ("run1", "run2"), "main", "compliant", "risk", "failure", "success", +1, False),
    ("G3", "E2 borderline agent: risk at the time, failure − success", "e2", ("run1", "run2"), "main", "borderline", "risk", "failure", "success", +1, False),
    ("G3", "E3: risk at the time, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "risk", "harm", "payoff", +1, False),
    ("G3", "E3: decision quality, harm − payoff", "e3", ("run1", "run2"), "main", "borderline", "quality", "harm", "payoff", -1, False),
    ("G4", "Rule purpose stated: violation, harm − payoff", "e3", ("s2-purpose", "s2-purpose-run2"), "main", "borderline", "violation", "harm", "payoff", +1, False),
    ("G4", "Rule purpose stated: change in harm − payoff from E3", "e3", ("s2-purpose", "s2-purpose-run2"), "main", "borderline", "violation", "harm", "payoff", 0, True),
    ("G5", "Neutral note: suspicion, no harm − neutral", "e5", ("s2-e5_neutral", "s2-e5_neutral-run2"), "main", None, "suspicion", "noharm", "neutral", -1, False),
    ("G5", "Neutral note: intent, no harm − neutral", "e5", ("s2-e5_neutral", "s2-e5_neutral-run2"), "main", None, "intent", "noharm", "neutral", -1, False),
    ("G5", "Neutral note: suspicion, neutral − no note", "e5", ("s2-e5_neutral", "s2-e5_neutral-run2"), "main", None, "suspicion", "neutral", "none", 0, False),
    ("G6", "Labelled scale: change in harm − payoff from E3", "e3", ("x1-labelled", None), "main", "borderline", "violation", "harm", "payoff", -1, True),
    ("G6", "Labels + sentence: change in harm − payoff from E3", "e3", ("x1-ignore", "x1-ignore-run2"), "main", "borderline", "violation", "harm", "payoff", -1, True),
    ("G7", "Think first: violation, harm − payoff", "e3", ("run1", None), "reasoning", "borderline", "violation", "harm", "payoff", +1, False),
    ("G7", "Think first: risk at the time, harm − payoff", "e3", ("run1", None), "reasoning", "borderline", "risk", "harm", "payoff", +1, False),
    ("G8", "E3: blame, payoff − no ending", "e3", ("run1", "run2"), "main", "borderline", "blame", "payoff", "omitted", -1, False),
    ("G8", "E3: risk at the time, payoff − no ending", "e3", ("run1", "run2"), "main", "borderline", "risk", "payoff", "omitted", -1, False),
]


def estimate(model, label, exp, arm, version, q, a, b, from_e3):
    if label is None:
        return None
    rows = answers(label, exp, model, arm=arm)[0]
    if rows is None:
        return None
    um = unit_means(select(rows, q, version))
    if from_e3:
        return change(um, unit_means(select(answers("run1", "e3", model)[0], q, version)), a, b)
    return contrast(um, a, b)


def verdict(first, second, sign):
    """Rule 1 on the Gemini first runs, then rule 2 on the models it was claimed on."""
    if sum(first[m] is not None for m in GEMINI) < 2:
        return "one model only (descriptive)", {}
    dirs = [direction(first[m]) for m in GEMINI]
    claim = sign if sign else (+1 if dirs.count(+1) >= 2 else -1 if dirs.count(-1) >= 2 else 0)
    if not claim or dirs.count(claim) < 2:
        return "not claimed", {}
    out = {}
    for m, d in zip(GEMINI, dirs, strict=True):
        if d == claim:
            out[m] = ("not re-run" if second[m] is None else
                      "confirmed" if direction(second[m]) == claim else "not confirmed")
    n_ok = sum(v == "confirmed" for v in out.values())
    word = "claimed" if sign else f"claimed ({'+' if claim > 0 else '−'})"
    tail = (f", confirmed {n_ok} of {len(out)}" if any(v != "not re-run" for v in out.values())
            else ", single run")
    return word + tail, out


def main():
    check_freeze()
    print("\n## Summary  (* = 95% interval excludes zero; Gemini cells: first run / re-run)\n")
    print("| | Test | Haiku | Sonnet | Opus | Hydrogen | Argon | Carbon | Gemini |")
    print("|---|---|---|---|---|---|---|---|---|")
    details = []
    for hyp, name, exp, (l1, l2), arm, version, q, a, b, sign, from_e3 in TESTS:
        d = digits_for(q)
        args = (exp, arm, version, q, a, b, from_e3)
        claude = {m: estimate(m, l1, *args) for m in CLAUDE}
        first = {m: estimate(m, l1, *args) for m in GEMINI}
        second = {m: estimate(m, l2, *args) for m in GEMINI}
        word, per = verdict(first, second, sign)
        gem = [fmt_short(first[m], d) + ("" if l2 is None else f" / {fmt_short(second[m], d)}") for m in GEMINI]
        print(f"| {hyp} | {name} | " + " | ".join(fmt_short(claude[m], d) for m in CLAUDE) + " | " + " | ".join(gem)
              + f" | {word} |")
        details.append((hyp, name, l2, first, second, per, d))
    print("\n## Gemini in detail  (first run; re-run; rule 2 for each model the effect was claimed on)\n")
    for hyp, name, l2, first, second, per, d in details:
        print(f"- **{hyp}, {name}**")
        for m in GEMINI:
            tail = f"; re-run {fmt_full(second[m], d)}" if l2 else ""
            print(f"  - {SHORT_NAMES[m]}: {fmt_full(first[m], d)}{tail}{'  → ' + per[m] if m in per else ''}")
    print("\n## Unparsed answers (Gemini)\n")
    seen = set()
    for _, _, exp, labels, arm, *_ in TESTS:
        for label in labels:
            if label and (label, exp, arm) not in seen:
                seen.add((label, exp, arm))
                counts = [answers(label, exp, m, arm=arm) for m in GEMINI]
                if any(r is not None for r, _ in counts):
                    print(f"- {exp} {label} ({arm}): " + ", ".join(
                        f"{SHORT_NAMES[m]} {bad if rows is not None else '—'}"
                        for m, (rows, bad) in zip(GEMINI, counts, strict=True)))


if __name__ == "__main__":
    main()
