"""Read answers from Inspect logs into plain rows, one per parsed answer.

Row fields: exp, model, reasoning, unit, version, cond, wording, question, answer, reason, epoch,
detected (E4), others (E4: other tickets listed), thought (whether the model used reasoning tokens).
Unparsed answers are counted and left out, as pre-registered.

  load(paths)                  rows from given log files
  answers(label, exp, model)   rows for one labelled run in the run index
  frame(exp, labels, models)   a pandas DataFrame over several runs, with a "label" column
"""

from functools import cache

from inspect_ai.log import read_eval_log

from outcome_bias import runlog
from outcome_bias.models import CLAUDE


@cache
def _load_one(path: str):
    rows, bad = [], 0
    log = read_eval_log(path)
    model = log.eval.model.split("/")[-1]
    reasoning = log.eval.task_args.get("reasoning", "none")
    for s in log.samples or []:
        md = s.metadata
        score = next(iter(s.scores.values())) if s.scores else None
        sm = score.metadata if score else {}
        if not sm.get("parsed"):
            bad += 1
            continue
        rows.append(dict(exp=md["exp"], model=model, reasoning=reasoning, unit=md["unit"], version=md["version"],
                         cond=md["cond"], wording=md.get("wording", 0), question=md["question"], answer=sm["answer"],
                         reason=score.explanation or "", epoch=s.epoch,
                         detected=sm.get("detected"), others=sm.get("others_listed"),
                         thought=(getattr(s.output.usage, "reasoning_tokens", 0) or 0) > 0))
    return tuple(rows), bad


def load(paths):
    """(rows, number unparsed) for the given log files, pooled."""
    rows, bad = [], 0
    for p in paths:
        r, b = _load_one(str(p))
        rows += r
        bad += b
    return rows, bad


def answers(label, exp, model=None, arm="main"):
    """Rows for one labelled run in the run index, or (None, 0) if it has not been run."""
    paths = runlog.logs(label=label, exp=exp, arm=arm, model=model)
    return load(paths) if paths else (None, 0)


def frame(exp, labels=("run1", "run2"), arm="main", models=CLAUDE):
    """All parsed answers of one experiment over the given run labels, as a DataFrame.
    Only the given models (short names; Claude by default). The model column holds the short name."""
    import pandas as pd

    parts = []
    for label in labels:
        for run in runlog.find(label=label, exp=exp, arm=arm):
            if run.model not in models:
                continue
            rows, _ = _load_one(str(run.path))
            df = pd.DataFrame(list(rows))
            df["label"] = label
            df["model"] = run.model
            parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def select(rows, question=None, version=None, model=None):
    return [r for r in rows
            if (question is None or r["question"] == question) and (version is None or r["version"] == version)
            and (model is None or model in r["model"])]
