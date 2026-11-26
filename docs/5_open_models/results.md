# Results: an open-weight check, Inkling 2 Mini

**Why:** the Gemini comparison ([4_gemini](../4_gemini/results.md)) found one difference from Claude: a payoff lowered blame and hindsight risk in all three Gemini models, and in none of Claude's. With two families there was no telling which one was unusual. This adds a model from a third developer, on the test that separates them.

**No written plan.** This run was chosen after the Gemini results were known, to answer that one question. It is a single run with no re-run, so it describes; it does not claim effects under the main plan's rules.

**The run:**
- **When:** 22 to 23 November 2026, 19:33 to 08:54 UTC.
- **Model:** Inkling 2 Mini (Thinking Machines, open weights), served by Ollama 0.40.17 on a local Mac (MLX runner, 8,192-token context). Its thinking cannot be switched off: with no effort setting, "none" or `think=false` it still spent 280 to 435 hidden tokens on a short prompt, so it ran at effort "low", as Opus and Gemini Hydrogen did. About 340 output tokens per answer.
- **What ran:** E3 (`e3_consequences`), the questions `violation`, `blame` and `risk` only, three samples per item: 1,080 answers, run label `run1`. All 1,080 parsed; no errors.
- **Cost:** no API cost. About 35 seconds per answer, one request at a time (the server did not run requests in parallel, even with `OLLAMA_NUM_PARALLEL=4`).

**Reproduce:**
- `python -m outcome_bias.run e3_consequences --models inkling-2-mini --questions violation,blame,risk --label run1`, with `OLLAMA_BASE_URL` in `.env`;
- `python -m outcome_bias.analysis.open_comparison`: the tables below.

**How to read the numbers:**
- Differences are in points on the question's 0–100 scale, averaged over E3's 21 borderline scenarios, first runs for every model.
- Each difference comes with a bootstrap 95% interval over scenarios. \* means the interval excludes zero.
- The Claude and Gemini cells are the same first runs as in Figure 7 and the Gemini results; their re-runs are in those documents.

## Summary

| Question | Claude (Haiku, Sonnet, Opus) | Gemini (Hydrogen, Argon, Carbon) | Inkling 2 Mini |
|---|---|---|---|
| **Violation, harm − no ending** | +24\*, +15\*, +4\* | +12\*, +10\*, +4\* | **+11\*** [+6, +17] |
| **Violation, payoff − no ending** | +1, −3, +2 | −3\*, +3, −2 | **−2** [−6, +1] |
| **Blame, payoff − no ending** | −1, −1, 0 | −11\*, −11\*, −7\* | **+1** [−3, +4] |
| **Risk at the time, payoff − no ending** | −5, −3, −5\* | −17\*, −11\*, −10\* | **−5\*** [−9, −1] |
| Blame, harm − no ending | +21\*, +15\*, +11\* | +23\*, +18\*, +12\* | +15\* [+11, +20] |
| Risk at the time, harm − no ending | +31\*, +25\*, +9\* | +23\*, +13\*, +11\* | +11\* [+7, +17] |

**Inkling sides with Claude.**
- **Verdict:** harm raised the violation estimate by 11 points, in 19 of the 21 scenarios and lower in none. A payoff did not lower it. This is the post's first finding, now in seven models.
- **Blame:** a payoff left blame where it was (+1). The interval rules out a drop of more than about 3 points, against Gemini's 7 to 11.
- **Risk:** a payoff lowered risk at the time by about 5 points, within Claude's 3 to 5 and well short of Gemini's 10 to 17.

So of the three developers' models, Gemini is the one that lets good luck excuse the agent, not Claude.

**Not a floor effect.** With no ending, Inkling was the harshest of the seven judges, so a payoff had the most room to lower its scores:

| Mean with no ending | Haiku | Sonnet | Opus | Hydrogen | Argon | Carbon | Inkling |
|---|---|---|---|---|---|---|---|
| Violation | 48.8 | 49.9 | 70.2 | 62.2 | 64.4 | 72.2 | **75.7** |
| Blame | 37.8 | 33.1 | 53.1 | 37.2 | 50.2 | 56.4 | **60.4** |
| Risk at the time | 42.6 | 28.7 | 50.3 | 46.0 | 40.5 | 40.8 | **71.8** |

The high starting point may cap Inkling's harm effects instead: its answers cluster between 70 and 95.

## Limits

- **One model, one run, one experiment.** No re-run, and none of E1, E2, the follow-ups or the explanation analysis. In particular, the human stories (E1) were not run, so whether Inkling lets a good ending lower blame for a person, as all six Claude and Gemini models do, is unknown.
- **Chosen after seeing Gemini's results**, to settle one question, with no written plan.
- **One open model.** Other open models, or larger ones, could behave differently.

## What happened during the run

Answers took about 35 seconds each, except for two interruptions. Neither lost or changed an answer:
- **Server slowdown.** From 20:19 UTC the server slowed to two to three times its normal time per answer. One request timed out four times before succeeding, 21 minutes later. A server restart at about 21:00 fixed it.
- **The client laptop slept.** It slept from 21:43 to 23:21 UTC. The request in flight timed out at 23:31 and was retried, and the run carried on.

The retries are logged with each answer.
