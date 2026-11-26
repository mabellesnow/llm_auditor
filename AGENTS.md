# Working in this repository

A research codebase: experiments that show LLM judges agent transcripts identical except for how things turned out, and the analyses of their answers. The README has the layout and commands; `docs/README.md` maps every study to its stimuli, plan, results and run labels.

## Rules that protect the results

1. **Never change what a logged run saw.** Stimulus files (`outcome_bias/stimuli/`) are frozen in `stimuli/hashes.json`, and every study's prompts are pinned by digests in `tests/test_prompts.py`. Refactor prompt assembly (`prompts.py`, `studies/`) only if those digests still match. A new study gets new stimulus files and a new study module; it never edits old ones.
2. **The unit of analysis is the scenario**, not the answer: average answers per (scenario, ending) with `stats.unit_means`, then compare endings with `stats.contrast` or `stats.change`. Don't bootstrap over individual answers.
3. **Unparsed answers are excluded and counted**, never filled in. Every report prints the count.
4. **Plans are frozen.** Don't edit `docs/*/plan.md` or `plan_hashes.json`. Results documents quote numbers printed by the analysis modules; when code changes a number, say so in the document that quotes it.
5. **Run labels are historical.** Rows in `logs/exp_runs.tsv` keep the label they were run under (`x1-`, `s2-` prefixes included).
6. **Model calls cost money.** Anything that runs `python -m outcome_bias.run` without `--limit` calls a paid API (except `inkling-2-mini`, served locally). Estimate the cost from `models.py`'s batch prices and get the user's go-ahead first; smoke-test with `--limit 3`.
7. **Secrets live in `.env`.** Never print its values.

## Where things go

| To add | Put it in |
|---|---|
| a model | `models.py` (`MODELS`, and a family tuple if it belongs to one); smoke-test it before a full run |
| a study | stimuli in `stimuli/<study_id>/`, `studies/<study_id>.py` with `build()`, a row in `studies/STUDIES`, a `@task` in `tasks.py` (Inspect finds tasks by reading that file, so each is written out), and its digest in `tests/test_prompts.py` |
| an analysis | `analysis/<name>.py` with a `main()`; read answers with `analysis.load`, compute with `stats.py`, write tables with `paths.extra_table` |
| a figure | `figures.py`, appended to `ALL` |

## Checks

```bash
.venv/bin/pytest            # offline, a few seconds; needs no logs
.venv/bin/ruff check .
python -m outcome_bias.verify   # needs logs/: rebuilds every logged prompt from the current code (a few minutes)
```

Run all three after any change to `prompts.py`, `studies/`, `stimuli/`, `scoring.py` or `stats.py`. If an analysis' output should not change, run it before and after and diff the output.
