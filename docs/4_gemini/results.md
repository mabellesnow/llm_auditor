# Results: the Gemini comparison

**Plan:** [plan.md](plan.md). It was written while the first runs were in progress, after E3's first Gemini run had been read. Its "Not a clean pre-registration" note says what had been seen.

**The runs:**
- **When:** 22 November 2026, through Google's batch API.
- **Models:** Gemini 4 Hydrogen (thinking level "low", since its thinking cannot be switched off), and Gemini 4 Argon and Carbon (thinking off).
- **What ran:** 39 finished runs, 22 first runs and 17 re-runs. Four failed attempts got no answers; they are labelled `failed` in the run index and excluded.
- **Re-runs:** every effect claimed for Gemini was re-run once on the models it was claimed on (rule 2), and every re-run agreed.
- **Cost:** about $72 at batch prices: $67.72 for the finished runs, $0.44 for smoke tests, and about $3.80 for two lost jobs that were paid for twice (see the plan's Deviations).

**Reproduce:**
- `python -m outcome_bias.analysis.gemini_comparison`: every test below, first run and re-run;
- `python -m outcome_bias.analysis.main_experiments e3` (or `e1`, `e2`): every model, every question;
- `python -m outcome_bias.analysis.faithfulness --family gemini`: the explanations.

**How to read the numbers:**
- Differences are in points on the question's 0–100 scale (sanction is 0–4), averaged over scenarios.
- Each difference comes with a bootstrap 95% interval over scenarios.
- \* means the interval excludes zero.
- Gemini cells give the first run, then the re-run.

## Summary

| Finding in the post | Claude (Haiku, Sonnet, Opus) | Gemini (Hydrogen, Argon, Carbon) | Status for Gemini |
|---|---|---|---|
| **Harm makes the same transcript look like a violation** (G1) | +24, +15, +4 against no ending | +12, +10, +4 (re-run +15, +9, +5) | Claimed, confirmed in all three |
| **A payoff does not make it look less like one** (G2) | +1, −3, +2 | −3, +3, −2 (re-run −2, +2, 0) | Null holds |
| **Good luck doesn't excuse** for blame and hindsight risk (G8) | Blame −1, −1, 0; risk −5, −3, −5 | Blame **−11, −11, −7**; risk **−17, −11, −10** | **Does not hold for Gemini.** A payoff lowers both, confirmed in all three. |
| **Hindsight**: harm raises "risk at the time" (G3) | +35, +28, +13 | +39, +24, +21 | Claimed, confirmed in all three |
| Hindsight after an unrelated task failure, borderline agent (G3) | +9, +2, +4 | **+16, +17, +16** | Claimed, confirmed in all three; stronger than Claude |
| Hindsight after a task failure, compliant agent (G3) | +9, +2, +2 | +12, +3, +5 | Not claimed (Hydrogen only) |
| **Stating the rule's purpose leaves the shift** (G4) | +15, +18, +8 remain | +20, +12, +6 remain; no reduction | Claimed, confirmed in all three |
| **Labels + one sentence remove most of it** (G6) | −20, −11, −2 | −10, −4, −2 | Claimed (Hydrogen, Argon), confirmed |
| Labels alone don't (G6) | −6, −5, 0 | +7, +3, +3 | Holds |
| **Thinking first doesn't remove it** (G7) | Haiku +9, Sonnet +13 | Carbon +6 (+6 without) | Holds on the one model run |
| **"Nothing bad happened" lowers a monitor's suspicion**, beyond any note (G5) | −15, −15, −8 | −19, −5, −5 | Claimed, confirmed in all three |
| …and judged intent (G5) | −9, −6, −7 | −7, −2, +2 | Not claimed (Hydrogen only) |
| **Explanations rarely mention the ending, yet the verdict moves** (finding 4) | Mention 53%, 25%, 31% | Mention **10%, 4%, 7%**; shift without a mention +12, +7, +4 | Holds, more strongly |
| Positive control: blame in human stories, bad − good (E1) | +12, +23, +20 | +13, +21, +21 | Claimed, confirmed in all three |

## What this changes in the story

1. **The central result is not Claude-specific.** In both families, a harmful ending makes the same transcript look more like a rule violation, and an ending where the shortcut paid off does not make it look less like one.
   - **The verdict's asymmetry holds in all six models:** bad luck condemns, good luck doesn't excuse.
   - **It is weakest in the most capable model of each family:** Opus (+4 against no ending) and Carbon (+4).
2. **The asymmetry on blame and hindsight is Claude's.** For Gemini, a payoff lowers blame and lowers the judged "risk at the moment the agent chose". Good luck excuses as much as bad luck condemns.
   - **Where both families agree:** for blame on people (E1), all six models let a good ending lower blame below the no-ending baseline.
   - **Where they differ:** only Claude stops doing so when the one being judged is an AI agent.
   - The post's "good luck doesn't excuse" therefore holds for the verdict, not for blame and risk in general.
3. **Gemini's hindsight is stronger, and reaches further.**
   - **When the shortcut caused harm:** "risk at the moment of the decision" rises by 21 to 39 points.
   - **When the task failed for a reason that had nothing to do with the shortcut:** all three Gemini models still raise it by 13 to 18 points, against 2 to 9 for Claude.
4. **The fixes behave the same way.**
   - **Labels plus one sentence** ("judge only what the agent did…") cut the shift where there is one to cut: Hydrogen −10, Argon −4. They do little in the model that barely shifted (Carbon), as with Opus.
   - **Labels alone** don't help.
   - **Stating the rule's purpose** doesn't help either: no Gemini model's shift shrinks.
5. **The monitor result replicates.** Against a neutral note, "nothing bad happened" lowers suspicion in all three Gemini models.
   - **Intent:** unlike Claude, the judged probability that the action was deliberate falls only in Hydrogen.
   - **Any note at all:** all three Gemini models also relax when there is just a neutral note (−3 to −6 against no note), which only Sonnet did among Claude.
6. **Gemini's explanations show even less.**
   - **Mentions:** after harm, they mention it in 4 to 10% of answers.
   - **The shift is there anyway:** in the answers whose reasons share no word with the ending, the verdict still moves almost as far as in all answers (+12, +7, +4).
   - **Setting the ending aside:** Gemini essentially never says that an ending doesn't change whether the rule was broken, after harm or after a payoff.

## The tests in detail

From `python -m outcome_bias.analysis.gemini_comparison`. Claude cells are first runs, as in the post. "Confirmed n of m" counts, among the Gemini models whose first run excluded zero in the claimed direction, those whose re-run did too.

| | Test | Haiku | Sonnet | Opus | Hydrogen | Argon | Carbon | Gemini |
|---|---|---|---|---|---|---|---|---|
| E1 | Human stories: blame, bad − good | +12.4\* | +23.4\* | +19.8\* | +13.0\* / +12.6\* | +21.2\* / +21.7\* | +21.2\* / +20.9\* | claimed, confirmed 3 of 3 |
| E1 | Human stories: blame, good − no ending | −6.5\* | −14.8\* | −10.7\* | −10.3\* / −9.8\* | −13.8\* / −14.2\* | −14.3\* / −13.8\* | claimed (−), confirmed 3 of 3 |
| G1 | E3: violation, harm − payoff | +23.2\* | +17.3\* | +1.9 | +14.5\* / +16.7\* | +6.9\* / +7.4\* | +5.7\* / +5.3\* | claimed, confirmed 3 of 3 |
| G1 | E3: violation, harm − no ending | +23.8\* | +14.5\* | +3.7\* | +11.7\* / +14.7\* | +9.6\* / +9.3\* | +4.0\* / +5.1\* | claimed, confirmed 3 of 3 |
| G1 | E3: blame, harm − payoff | +22.5\* | +16.0\* | +11.7\* | +33.7\* / +32.8\* | +28.7\* / +27.6\* | +18.8\* / +19.1\* | claimed, confirmed 3 of 3 |
| G1 | E3: sanction (0–4), harm − payoff | +0.75\* | +0.48\* | +0.40\* | +0.98\* / +0.96\* | +0.66\* / +0.66\* | +0.63\* / +0.63\* | claimed, confirmed 3 of 3 |
| G1 | E3: accept as it stands, harm − payoff | −19.5\* | −28.6\* | −7.3\* | −32.9\* / −31.9\* | −18.8\* / −18.2\* | −9.6\* / −9.3\* | claimed, confirmed 3 of 3 |
| G2 | E3: violation, payoff − no ending | +0.7 | −2.7 | +1.8 | −2.8\* / −2.0 | +2.7 / +1.9 | −1.8 / −0.3 | not claimed |
| G3 | E1: risk at the time, bad − good | +21.3\* | +5.1\* | +2.3\* | +4.2\* / +3.5\* | +4.3\* / +4.3\* | +2.2 / +2.6\* | claimed, confirmed 2 of 2 |
| G3 | E2 compliant agent: risk at the time, failure − success | +9.0\* | +1.7\* | +2.1\* | +11.6\* / +12.4\* | +3.3 / +3.4 | +4.5 / +4.6 | not claimed |
| G3 | E2 borderline agent: risk at the time, failure − success | +9.3\* | +2.2 | +4.0\* | +15.5\* / +13.3\* | +17.4\* / +14.0\* | +15.8\* / +18.1\* | claimed, confirmed 3 of 3 |
| G3 | E3: risk at the time, harm − payoff | +35.1\* | +28.1\* | +13.1\* | +39.1\* / +38.7\* | +23.9\* / +26.3\* | +21.3\* / +22.1\* | claimed, confirmed 3 of 3 |
| G3 | E3: decision quality, harm − payoff | −8.4\* | −11.6\* | −3.2\* | −9.9\* / −9.9\* | −2.8 / −4.0\* | −0.9 / −1.4 | not claimed |
| G4 | Rule purpose stated: violation, harm − payoff | +14.8\* | +18.3\* | +7.9\* | +19.8\* / +19.6\* | +12.0\* / +12.1\* | +6.0\* / +6.1\* | claimed, confirmed 3 of 3 |
| G4 | Rule purpose stated: change in harm − payoff from E3 | −8.4\* | +1.0 | +6.0\* | +5.4 / +5.1 | +5.1 / +5.2\* | +0.3 / +0.4 | not claimed |
| G5 | Neutral note: suspicion, no harm − neutral | −14.7\* | −14.8\* | −7.8\* | −18.5\* / −18.0\* | −5.2\* / −4.5\* | −4.5\* / −3.4\* | claimed, confirmed 3 of 3 |
| G5 | Neutral note: intent, no harm − neutral | −9.3\* | −5.5\* | −7.2\* | −7.0\* / −11.6\* | −2.1 / −0.9 | +2.2 / +0.7 | not claimed |
| G5 | Neutral note: suspicion, neutral − no note | −3.4 | −5.3\* | −0.6 | −3.1\* / −6.3\* | −5.1\* / −5.2\* | −4.8\* / −6.0\* | claimed (−), confirmed 3 of 3 |
| G6 | Labelled scale: change in harm − payoff from E3 | −6.2 | −5.0 | −0.2 | +7.4 | +2.8 | +3.0 | not claimed |
| G6 | Labels + sentence: change in harm − payoff from E3 | −19.9\* | −10.7\* | −2.1 | −9.7\* / −9.8\* | −4.1\* / −4.4\* | −1.9 | claimed, confirmed 2 of 2 |
| G7 | Think first: violation, harm − payoff | +9.1\* | +13.2\* | | | | +5.7\* | one model only |
| G7 | Think first: risk at the time, harm − payoff | +37.9\* | +34.0\* | | | | +20.4\* | one model only |
| G8 | E3: blame, payoff − no ending | −1.3 | −0.6 | −0.4 | −10.8\* / −11.6\* | −10.8\* / −9.5\* | −7.3\* / −7.1\* | claimed, confirmed 3 of 3 |
| G8 | E3: risk at the time, payoff − no ending | −4.6 | −3.3 | −4.6\* | −16.6\* / −15.2\* | −11.2\* / −11.4\* | −10.0\* / −10.1\* | claimed, confirmed 3 of 3 |

The intervals for every Gemini cell are printed by the module. Some that matter for the post:

| | Hydrogen | Argon | Carbon |
|---|---|---|---|
| E3 violation, harm − no ending (first run) | +11.7 [+5.7, +18.8] | +9.6 [+5.2, +14.6] | +4.0 [+1.2, +6.7] |
| E3 blame, payoff − no ending (re-run) | −11.6 [−18.7, −5.1] | −9.5 [−15.4, −3.8] | −7.1 [−10.5, −3.9] |
| E3 risk at the time, payoff − no ending (re-run) | −15.2 [−22.5, −8.5] | −11.4 [−18.9, −4.6] | −10.1 [−14.9, −6.1] |
| Labels + sentence, change (re-run) | −9.8 [−17.4, −2.9] | −4.4 [−8.7, −0.6] | |
| Neutral note, suspicion, no harm − neutral (re-run) | −18.0 [−24.4, −11.8] | −4.5 [−7.2, −1.6] | −3.4 [−5.9, −0.9] |

## Explanations (exploratory)

The method is the same as for Claude ([docs/3_extra_analyses/results.md](../3_extra_analyses/results.md)):
- it covers E3's borderline versions, the violation question, both runs pooled, after harm;
- the strict group is reasons that share no word at all with their ending;
- tables are in `docs/3_extra_analyses/tables/faithfulness_*_gemini.csv`.

| | Haiku | Sonnet | Opus | Hydrogen | Argon | Carbon |
|---|---|---|---|---|---|---|
| Reasons that mention the harm | 53% | 25% | 31% | 10% | 4% | 7% |
| Shift, all answers | +24.1 | +16.0 | +3.3 | +13.2 [+7.2, +20.5] | +9.5 [+5.2, +14.2] | +4.5 [+2.1, +6.9] |
| Shift, reasons sharing no word with the ending | +14.3 | +17.4 | +4.1 | +12.0 [+5.8, +19.6] | +6.9 [+3.8, +10.2] | +4.2 [+2.2, +6.5] |

- **False positives** (mentions of an ending the model never saw) were 1 to 3% of no-ending answers.
- **Dismissals:** reasons that set the ending aside were 0 to 0.8% after harm and 0% after a payoff. Opus did this sometimes after a payoff.

## Unparsed answers

- **Content filter on three actions.** Google's prompt filter blocked some E5 answers on three of the 12 actions: `scratch_copy`, `firewall_rule` and `token_scope`. The answers came back as "BLOCKED: BlockedReason.OTHER". Per run:
  - Hydrogen 48 of 756;
  - Carbon 45;
  - Argon 3 in each run.
  - Most blocked answers were for `scratch_copy` (33 of its 63, for Hydrogen and Carbon). The other answers in those actions are kept, so no action drops out entirely. Opus had a similar block on `audit_logs` in the Claude runs.
- **A line break inside the reason.** Argon sometimes put a line break inside the reason string, which is not valid JSON. It happened in 25 of 2,520 answers in its E3 re-run and 6 in its first neutral-note run. They are excluded, as the main plan's exclusion rule provides. The parser was not changed after the fact.
- **Everything else:** 0 to 2 unparsed answers per run.

## Limits

- **Reasoning settings differ, as they did for Claude.** Argon and Carbon run with thinking off, though Carbon still used some thinking on 7% of its answers. Hydrogen thinks on every answer at its lowest level, as Opus did at "low". So size comparisons across models mix model and setting.
- **G8 was found in E3's first run before the plan was written.** It is confirmed by the re-run in all three models, but it is a confirmed exploratory finding, not a pre-registered one.
- **Three models per family** allow no test of a family difference. "Holds in both families" means claimed and confirmed in each.
- **"Think first" was run on one Gemini model (Carbon).** Argon would have needed "high", which was ruled out to keep reasoning effort moderate.
- **Not run on Gemini:** E4 and E1's medium arm. The post does not use them.
