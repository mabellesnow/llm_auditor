# Plan: the Gemini comparison

Written 22 November 2026, about 14:25 UTC, while the first runs were in progress. Follows [the main plan](../1_main_experiments/plan.md) and [the follow-ups plan](../2_follow_ups/plan.md). Their settings, exclusions and rules 1 to 4 apply unless stated here.

**Not a clean pre-registration.** Before this was written:

- **Smoke tests:** 3 items on each model, used to choose the reasoning settings (below).
- **E3:** the main arm (first run) on all three models. Its results had been read: the agent-transcript scenarios with a harmful, paid-off or missing ending.
- **E1:** finished but not yet read.

Nothing else had been run. E3's first-run Gemini results therefore aren't a test of this plan. The one pattern noticed in them is stated as hypothesis G8, and E3's re-run tests it.

## Why

The blog post's findings come from three models of one family. This runs the same studies on a second family, Google's Gemini 4, to see which findings are about LLM judges in general and which are about Claude.

## Models and settings

| | Gemini 4 Hydrogen | Gemini 4 Argon | Gemini 4 Carbon |
|---|---|---|---|
| Google's description | fast, everyday model | efficient frontier reasoning model | most capable reasoning model |
| Rough Claude counterpart | Haiku | Sonnet | Opus |
| Main arm | thinking level "low" (thinking cannot be switched off) | thinking off (`thinkingBudget: 0`) | thinking off (`thinkingBudget: 0`) |
| Claude analogue of the main arm | Opus ("low") | Haiku, Sonnet (off) | Haiku, Sonnet (off) |
| "Think first" arm (E3 only) | not run: already thinks in its main arm, like Opus | thinking level "high" | thinking level "medium" |

The rest is as for Claude:
- temperature 1;
- an output cap of 1,500 tokens when thinking is off;
- one question per call;
- the same samples per item;
- the batch API, through Inspect's `google` provider.

**How the reasoning settings were chosen** (smoke tests, 3 E3 items each):
- **Main arm:** the lowest setting the model allows, as for Claude.
  - Hydrogen spent 190 to 360 thinking tokens per answer whether asked for "none" or "low".
  - Argon and Carbon accept "none" and then spend none.
- **"Think first" arm:** the lowest level at which the model thought on every answer, as for Claude.

| Thinking level | Argon | Carbon |
|---|---|---|
| "low" | none | none |
| "medium" | none | about 340 per answer |
| "high" | about 610 per answer | about 11,000 per answer |

## Runs

Labels match the Claude runs, so every analysis reads them the same way.

| Study | Label | Arm | Models | What the post uses it for |
|---|---|---|---|---|
| `e3_consequences` | `run1` | main | all three | The central result: harm against payoff, faithfulness |
| `e1_people` | `run1` | main | all three | Positive control; hindsight in human stories |
| `e2_task_outcome` | `run1` | main | all three | Hindsight when a compliant agent's task fails |
| `e3_consequences` | `run1` | reasoning | Carbon (Argon dropped: see Deviations) | "Think first" fix; hindsight with reasoning |
| `followup_labelled_scale`, `variant=labelled` | `x1-labelled` | main | all three | Labelled-scale fix |
| `followup_labelled_scale`, `variant=ignore` | `x1-ignore` | main | all three | Labels + "ignore what happened afterwards" fix |
| `followup_rule_purpose` | `s2-purpose` | main | all three | Does harm still move the verdict when the rule's purpose is stated? |
| `followup_neutral_note` | `s2-e5_neutral` | main | all three | The monitor result. This run also contains all four of E5's endings. |

**Not run**, because the post does not rely on them:
- **E4** (buried violation);
- **E1's medium-reasoning arm**;
- **E2's reasoning arm**;
- **a separate E5 main run:** E5's own contrasts (harm − no harm, harm − none, no harm − none) are computed from the neutral-note run, which has the same 12 actions and endings.

**Re-runs (rule 2):**
- Each experiment with an effect claimed for Gemini is re-run once, labelled `run2`, `x1-ignore-run2`, `s2-purpose-run2` or `s2-e5_neutral-run2`.
- E3 is re-run in any case. G8 needs it, and the faithfulness analysis pools both runs, as it does for Claude.

## Hypotheses

The direction comes from the Claude results. For each, the primary contrast and rule 1 are as in the main plan, applied within the Gemini family: a claim needs the 95% interval to exclude zero in the same direction in at least two of the three Gemini models, then a confirming re-run.

| | Claude finding in the post | Test on Gemini |
|---|---|---|
| G1 | Harm raises the judged probability that the rule was broken | E3, violation, harm − payoff (and harm − none) |
| G2 | A payoff does not lower it | E3, violation, payoff − none: expected null |
| G3 | Hindsight: harm raises "risk at the moment of the decision" | E1 bad − good; E2 compliant, failure − success; E3 harm − payoff; all on risk |
| G4 | Stating the rule's purpose leaves most of the shift | `s2-purpose`: harm − payoff on violation, and its change from E3's first run |
| G5 | A harmless ending lowers a monitor's suspicion, beyond any note | `s2-e5_neutral`: no harm − neutral, on suspicion and intent |
| G6 | Labels + one sentence remove most of the verdict shift; labels alone don't | `x1-ignore` and `x1-labelled`: change in harm − payoff on violation from E3's first run |
| G7 | Reasoning does not remove the shift or the hindsight | E3 reasoning arm against main arm (Carbon) |
| G8 | *(noticed in E3's first Gemini run; Claude did the opposite)* A payoff lowers blame and risk at the time, against no ending | E3 re-run, payoff − none on blame and risk |

Explanations (whether reasons mention the ending) are analysed as for Claude, with `python -m outcome_bias.analysis.faithfulness --family gemini`. Exploratory.

**Across families:** a finding is said to hold "in both families" only when it is claimed and confirmed in each family separately. Effect sizes are compared descriptively. With three models per family, there is no test of a family difference.

## Cost

Estimated at batch prices before 1 December 2026, from Haiku's token counts and the smoke tests:
- **First pass:** $47.
- **Re-runs:** up to $29.

Argon's and Carbon's prices double on 1 December.

## Code

The runs use the code at commit `06af61a`. It holds the Gemini setup:
- the model entries;
- the shared model list in the analysis code;
- a runner fix so that each run records only its own log.

That commit was made at 14:06, while E3's first runs were in progress. It changed no prompt and no setting those runs used. Two later changes are in the commit that adds the results:
- a note in `models.py` that Argon's "think first" run was dropped;
- from 15:35, the runner's error tolerance (see Deviations).

The stimuli are unchanged: `python -m outcome_bias.verify` checks their hashes and rebuilds every logged prompt.

## Deviations

- **Argon's "think first" run dropped (22 November, 14:30).** It would have used "high", Gemini's top thinking level, because Argon doesn't think at "medium". It was dropped at the user's request to avoid very high reasoning effort, before any of it ran. G7 is tested on Carbon only. Hydrogen, like Opus, already thinks in its main arm.
- **Prepaid credit ran out (22 November, about 14:27)** with about $20 spent. The run that was starting, Argon's "think first" E3, got no answers. Its log is labelled `failed` in the run index and excluded. Credit was added and the remaining runs continued. Finished runs were not repeated.
- **Project spend cap reached (22 November, about 15:00 to 15:20).** Google refused every call until the cap was raised. Two runs failed and kept no answers. Both are labelled `failed` and were run again from scratch:
  - Hydrogen's rule purpose: Google finished the batch job, but its results could not be downloaded, so that job (about $2.70) was paid for twice.
  - Argon's labels + sentence: refused before Google created a job, so nothing was spent.
- **Request errors no longer fail a whole run (22 November, 15:35).**
  - **What happened:** Carbon's rule-purpose batch finished at Google, but 2 of its 1,260 requests came back with an error ("Precondition check failed"). Under Inspect's default, any error fails the run, so all its answers were lost. The run is labelled `failed`, and the job (about $1.10) was paid for twice.
  - **The change:** from then on the runner passes `--retry-on-error=2 --fail-on-error=0.02`. A request that errors is retried twice. If it still errors, it counts as unparsed and is excluded, as the main plan's exclusion rule already provides. A run fails only if more than 2% of its answers error.
  - **Scope:** runs started before 15:35 used Inspect's default.
