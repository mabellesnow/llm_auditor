# Docs

Folders are numbered in the order the work happened. Plans were written and frozen before their runs, except the Gemini plan, written after its first E3 run (it says what had been seen), and the open-weight check, which had none. Results were written after.

| Folder | What it covers | Plan | Results |
|---|---|---|---|
| **1_main_experiments** | E1 to E5, five pre-registered experiments, plus the labelled-scale follow-up on Haiku (called X1 inside the documents) | [plan.md](1_main_experiments/plan.md) | [results.md](1_main_experiments/results.md) |
| **2_follow_ups** | Four runs that closed the gaps E1 to E5 left, called parts A to D (and "stage 2") inside the documents: A, Opus re-runs; B, the labelled scale on all models; C, a neutral-note control for E5; D, stating each rule's purpose | [plan.md](2_follow_ups/plan.md) | [results.md](2_follow_ups/results.md) |
| **3_extra_analyses** | Effect sizes and mixed models, which scenarios tip, whether explanations admit the swing. On the existing logs; exploratory | | [results.md](3_extra_analyses/results.md), `tables/` |
| **4_gemini** | The studies the post relies on (E1, E2, E3, the three follow-ups), re-run on a second model family: Gemini 4 Hydrogen, Argon and Carbon. The plan was written after E3's first Gemini run, and says so | [plan.md](4_gemini/plan.md) | [results.md](4_gemini/results.md); explanation tables in `3_extra_analyses/tables/*_gemini.csv` |
| **5_open_models** | E3's violation, blame and risk questions on an open-weight model, Inkling 2 Mini, served locally with Ollama: does it side with Claude or Gemini on whether good luck excuses? One run, chosen after the Gemini results, no plan | | [results.md](5_open_models/results.md) |
| **posts** | The write-up for general readers, and its figures | | [the_judge_who_read_the_ending.md](posts/the_judge_who_read_the_ending.md) |
| **background** | Prior work; ideas for turning this into a paper | | [prior_work.md](background/prior_work.md), [roadmap.md](background/roadmap.md) |

## Each study: where its pieces live

The study id is used everywhere: the stimulus folder, the code module, and the Inspect task.

| Study id | Question | Stimuli (in `outcome_bias/stimuli/`) | Docs | Run labels (logs/exp_runs.tsv) |
|---|---|---|---|---|
| `e1_people` | Do these models judge people by outcomes? (positive control) | `e1_people/` | 1 | e1: `run1`, `run2`; arm `medium` |
| `e2_task_outcome` | Does how the task went change how a shortcut is judged? | `agent_transcripts/` | 1; Opus re-run in 2 (part A) | e2: `run1`, `run2`; arm `reasoning` |
| `e3_consequences` | Does what the shortcut caused change it? | `agent_transcripts/`, `e3_consequences/` | 1; Opus re-run in 2 (part A) | e3: `run1`, `run2`; arm `reasoning` |
| `e4_buried_violation` | Does a good-session note hide a buried violation? | `e4_buried_violation/` | 1 | e4: `run1` |
| `e5_intent` | Does chance harm make an action look deliberate? | `e5_intent/` | 1 | e5: `run1`, `run2` |
| `followup_labelled_scale` | Is E3's verdict shift the unlabelled scale? Does an instruction remove it? | `followup_labelled_scale/` | 1 (Haiku, "X1"), 2 (part B) | e3: `x1-labelled`, `x1-ignore`, `x1-ignore-run2` |
| `followup_neutral_note` | Is E5's "no harm" relief the outcome, or any note? | `followup_neutral_note/` | 2 (part C) | e5: `s2-e5_neutral`, `s2-e5_neutral-run2` |
| `followup_rule_purpose` | Does harm still move the verdict when the rule's purpose is stated? | `followup_rule_purpose/` | 2 (part D) | e3: `s2-purpose`, `s2-purpose-run2` |

Run labels are the names recorded in the logs when each run happened, so they keep their original prefixes (`x1-`, `s2-`). The Gemini and Inkling runs reuse the same labels; the run index's model column (`gemini-4-…`, `inkling-2-mini`) tells them apart.

## Checking the stimuli

`outcome_bias/stimuli/hashes.json` holds the SHA-256 of every stimulus file. `python -m outcome_bias.verify` checks those hashes, then rebuilds every prompt in every logged run from the current code and compares it with what the model saw.

`tests/test_prompts.py` pins every study's prompts by digest as well, so `.venv/bin/pytest` catches a change to what the models see without needing the logs.

The per-plan hash files (`1_main_experiments/plan_hashes.json`, `2_follow_ups/plan_hashes.json`) are kept as written. They hash the Python files the stimuli lived in at the time.

## Names in older documents

The plans are left exactly as they were frozen, and the results quote the paths of their day. This maps those names to where things are now. Nothing the models saw has changed: after each reorganisation, every logged prompt (54 runs) was rebuilt from the new code and matched.

| In older documents | Now |
|---|---|
| `notes/prereg_e1_e5.md`, `notes/results_e1_e5.md`, `docs/e1_e5/` | `docs/1_main_experiments/` |
| `notes/prereg_stage2.md`, `docs/stage2/` | `docs/2_follow_ups/` |
| `docs/secondary/` | `docs/3_extra_analyses/` |
| `notes/prior_work.md`, `docs/reference/`, `docs/roadmap.md` | `docs/background/` |
| `stimuli/`, `docs/freeze.json` | `outcome_bias/stimuli/`, `outcome_bias/stimuli/hashes.json` |
| `stimuli/agent_audit/`, `outcome_bias/scenarios_v2.py` | `outcome_bias/stimuli/agent_transcripts/` |
| `annotations/agent_audit.yaml` | `outcome_bias/analysis/scenario_codes.yaml` |
| X1, `x1_labelled_scale`, `outcome_bias/exp_anchor.py`, `anchored` | `followup_labelled_scale` |
| stage 2 C, `s2c_neutral_note`, `e5_neutral` | `followup_neutral_note` |
| stage 2 D, `s2d_rule_purpose`, `purpose` | `followup_rule_purpose` |
| `outcome_bias/exp_e1.py` … `exp_e5.py`, `experiments.py`, `experiment` | `outcome_bias/studies/`, `prompts.py`, `scoring.py`, `tasks.py` |
| `outcome_bias/exp_analysis.py`, `analysis/e1_e5.py` | `outcome_bias/analysis/main_experiments.py` |
| `outcome_bias/stage2_analysis.py`, `analysis/stage2.py` | `outcome_bias/analysis/follow_ups.py` |
| `outcome_bias/x1_analysis.py`, `analysis/x1.py` | `outcome_bias/analysis/labelled_scale.py` |
| `outcome_bias/figures/post.py`, `figures/post/` | `outcome_bias/figures.py`, `docs/posts/figures/` |
| `run_exp.sh`, `run_anchor.sh`, `run_stage2.sh` | `python -m outcome_bias.run` |

## Retired

Moved out of the repository on 17 November 2026, because nothing uses them any more. They are in `archive/` on this machine (not in git), and in the git history at commit `fbf0b49`: restore any of them with `git checkout fbf0b49 -- <path>`.

- **The pilot ("Part 1")**, which asked only "was the rule broken?" after a one-line note on how the task went, and found nothing. It led to E1 to E5. `outcome_bias/part1/`, `stimuli/part1_pilot/`, `docs/part1_pilot/` (results, write-up draft, methods critique), `figures/part1/`.
- **The earlier blog post**, replaced by the one in `posts/`: `docs/post/outcome_bias_in_llm_auditors.md`, its figures `figures/e1_e5/`, and their code `outcome_bias/figures/e1_e5.py` and `style.py`.
