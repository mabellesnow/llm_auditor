"""Read answers from Inspect logs into plain rows, one per parsed answer.

Row fields: exp, model, reasoning, unit, version, cond, wording, question, answer, reason, epoch,
detected (E4), others (E4: other tickets listed), thought (whether the model used reasoning tokens).
Unparsed answers are counted and left out, as pre-registered.

Reading a log takes about two seconds, so the rows read from each log are kept in logs/.rows/, one JSON file
per log. A file is used only while the log's size and modification time, this module's source and Inspect's
version are the ones it was written from; otherwise the log is read again. Deleting the folder is always safe.

  load(files)                  rows from given log files
  answers(label, exp, model)   rows for one labelled run in the run index
  frame(exp, labels, models)   a pandas DataFrame over several runs, with a "label" column
"""

import hashlib
import json
import os
from functools import cache
from pathlib import Path

import inspect_ai
from inspect_ai.log import read_eval_log

from outcome_bias import paths, runlog
from outcome_bias.models import CLAUDE

# a change to this module or to Inspect invalidates the cache
_SOURCE = hashlib.sha256(Path(__file__).read_bytes() + inspect_ai.__version__.encode()).hexdigest()[:12]


@cache
def _load_one(path: str):
    """(rows, number unparsed) for one log, from the row cache when it is current."""
    log = Path(path)
    stat = log.stat()
    cached = paths.ROW_CACHE / f"{log.stem}.{stat.st_size}.{stat.st_mtime_ns}.{_SOURCE}.json"
    try:
        rows, bad = json.loads(cached.read_text())
        return tuple(rows), bad
    except FileNotFoundError:
        pass
    rows, bad = _read_log(path)
    paths.ROW_CACHE.mkdir(parents=True, exist_ok=True)
    for stale in paths.ROW_CACHE.glob(f"{log.stem}.*.json"):
        stale.unlink(missing_ok=True)
    tmp = cached.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps([rows, bad]))
    tmp.replace(cached)  # never leave a half-written cache file
    return tuple(rows), bad


def _read_log(path: str):
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
    return rows, bad


def load(files):
    """(rows, number unparsed) for the given log files, pooled."""
    rows, bad = [], 0
    for p in files:
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


def select(rows, question=None, version=None):
    """The rows for one question and one version (None = any)."""
    return [r for r in rows
            if (question is None or r["question"] == question) and (version is None or r["version"] == version)]
