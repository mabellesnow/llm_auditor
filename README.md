# Outcome bias in LLM auditors

Does an LLM that reviews an AI agent's work judge the same behaviour differently depending on how things turned out?

Every experiment uses the same move: show the model a transcript that is word-for-word identical except for its last line (how things turned out), ask one question per call, and compare the answers across endings, scenario by scenario.

**Start with the write-up:** [docs/posts/the_judge_who_read_the_ending.md](docs/posts/the_judge_who_read_the_ending.md).

Code and writeup assisted by Claude; research questions, experiment design and interpretation of results are my own.

## Layout

```
outcome_bias/      everything the code uses
  stimuli/         what the models read: transcripts, endings, questions, system prompts (+ their loader)
  studies/         one module per study: turns stimuli into prompts
  analysis/        one module per phase, plus the extra analyses
  figures.py       the blog post's figures
  ...              running, scoring, statistics, checks (table below)
tests/             fast offline tests: prompts unchanged, scoring, statistics, the run index, a mock run
docs/              what was planned and what was found, in the order it happened
  1_main_experiments/   E1 to E5: plan (written before the runs) and results
  2_follow_ups/         four runs that closed the gaps E1 to E5 left: plan and results
  3_extra_analyses/     effect sizes, which scenarios tip, whether explanations admit the swing
  4_gemini/             the same studies on Gemini 4 Hydrogen, Argon and Carbon: plan and results
  5_open_models/        E3's core test on an open-weight model, Inkling 2 Mini, served locally: results
  posts/                the blog post and its figures
  background/           prior work, ideas for next steps
logs/              Inspect logs, the run index and a cache of answers read from them (not in git)
archive/           retired work (the pilot, an earlier write-up) and personal notes (not in git)
```

[docs/README.md](docs/README.md) lists every study with its question, stimuli, code, plan, results and run labels.

## The studies

| Study | Question | Phase |
|---|---|---|
| `e1_people` | Do these models judge people by outcomes at all? (positive control) | 1 |
| `e2_task_outcome` | Does how the task went change how an agent's shortcut is judged? | 1 |
| `e3_consequences` | Does what the shortcut caused (a payoff, or harm) change it? | 1 |
| `e4_buried_violation` | Does a "good session" note make an auditor miss a buried violation? | 1 |
| `e5_intent` | Does chance harm make an action look deliberate to a monitor? | 1 |
| `followup_labelled_scale` | Is E3's verdict shift the unlabelled scale? Does one instruction remove it? | 1 (Haiku), 2 |
| `followup_neutral_note` | Is E5's relief after "no harm" the outcome, or any follow-up note? | 2 |
| `followup_rule_purpose` | Does harm still move the verdict when the rule's purpose is stated? | 2 |

The study id names its stimulus folder (`outcome_bias/stimuli/<id>/`, where it has one), its module (`outcome_bias/studies/<id>.py`) and its Inspect task (`tasks.py@<id>`). E2, E3 and two follow-ups share the agent transcripts in `outcome_bias/stimuli/agent_transcripts/`.

### Code, module by module

| Module | Job |
|---|---|
| `paths.py` | where stimuli, docs and logs live |
| `stimuli/` | the stimulus files, and `__init__.py` to load them |
| `prompts.py` | assemble prompts (transcripts, endings, E4 sessions) and wrap them as Inspect samples |
| `studies/` | one `build()` per study; `studies/__init__.py` lists them all |
| `tasks.py` | the Inspect task for each study |
| `scoring.py` | parse the JSON answer |
| `models.py` | model names and the reasoning setting of each arm |
| `run.py` | run a study on several models and record each run in the run index |
| `runlog.py` | read and write the run index |
| `stats.py` | per-scenario means, paired differences, bootstrap intervals |
| `analysis/` | `load.py` reads answers from logs; `main_experiments.py`, `labelled_scale.py` and `follow_ups.py` report each plan; `mixed_models.py`, `moderators.py` (with its scenario codes, `scenario_codes.yaml`) and `faithfulness.py` are the extra analyses; `gemini_comparison.py` and `open_comparison.py` set the other models beside Claude |
| `figures.py` | the blog post's figures, computed from the logs |
| `verify.py` | check stimulus hashes, and rebuild every logged prompt to confirm it is unchanged |
| `check_ollama.py` | check the local Ollama server, and whether it runs requests in parallel |

## Setup

```bash
uv sync
```

Put your API key in `.env` as `ANTHROPIC_API_KEY=...` (and `GEMINI_API_KEY=...` for Gemini models, `OPENAI_API_KEY=...` for OpenAI models). Gemini 4 Argon, Carbon and Neon need a Google project with billing on: on the free tier their quota is zero. For Inkling 2 Mini, served by Ollama, set `OLLAMA_BASE_URL=http://<host>:11434/v1`; `python -m outcome_bias.check_ollama` checks the server. Run every command from this folder: Inspect reads `.env` from where it starts.

On Python 3.14 for macOS, `uv sync` can hide the editable install's `.pth` file. If you see `No module named 'outcome_bias'`, run:

```bash
chflags nohidden .venv/lib/python3.*/site-packages/*.pth
```

## Running a study

```bash
python -m outcome_bias.run e3_consequences --batch
```

This runs the study on Haiku, Sonnet and Opus in their main arm (the lowest reasoning each allows) through the batch API, and records each run as `run1`. Options:

| Option | Meaning |
|---|---|
| `--models haiku sonnet opus` | which models (see `models.py`), or a family: `claude` (the default), `gemini`, `open` |
| `--arm main`, `medium` or `reasoning` | the reasoning setting |
| `--label run2` | the run's label in the run index (use it for re-runs) |
| `--batch` | use the provider's batch API (half price, slower) |
| `--epochs 1` | samples per item, instead of the study's pre-registered number |
| `--questions violation,blame` | only these questions (for slow models; the prompts are unchanged) |
| `--set variant=ignore` | a study parameter (`followup_labelled_scale`: `variant`; `e4_buried_violation`: `n_filler`) |
| `--limit 3` | a smoke test on the first 3 items, written to `logs/smoke/` and not recorded |

Every full run calls a paid API, except on `inkling-2-mini`. Smoke-test a model with `--limit 3` before its first full run.

## Analysing

```bash
python -m outcome_bias.analysis.main_experiments e3
```

```bash
python -m outcome_bias.analysis.main_experiments e3 --label run2
```

```bash
python -m outcome_bias.analysis.follow_ups
```

```bash
python -m outcome_bias.analysis.mixed_models
```

The pre-registered analyses (`main_experiments`, `follow_ups`, `labelled_scale`) report every model that has a run. The extra analyses (`mixed_models`, `moderators`, `faithfulness`) cover Claude by default; pass `--family gemini` for the Gemini models, which writes its tables with a `_gemini` suffix.

The first analysis after a run reads its log (about two seconds a log) and keeps the answers in `logs/.rows/`. Later analyses read them from there, and a changed log or a change to `analysis/load.py` makes them read the log again. Deleting `logs/.rows/` is always safe.

```bash
python -m outcome_bias.figures
```

```bash
python -m outcome_bias.verify
```

`inspect view` browses every transcript and answer.

## Checking a change

```bash
.venv/bin/pytest
```

```bash
.venv/bin/ruff check .
```

```bash
python -m outcome_bias.verify
```

The tests run offline in a few seconds and need no logs. They include a digest of every prompt of every study, so a change to what the models see fails them. `verify` needs the logs: it rebuilds every logged prompt from the current code and compares it with what the model saw (a few minutes). [AGENTS.md](AGENTS.md) lists the rules that protect the results and where new code goes.
