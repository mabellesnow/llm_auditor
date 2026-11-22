"""The run index, logs/exp_runs.tsv: one tab-separated row per model run.

  label  which run: run1, run2 (rule 2 re-run), x1-labelled, s2-purpose, ... or failed / partial
  exp    the experiment code in the items (e1 ... e5)
  arm    main, medium or reasoning (see models.py)
  model  short model name (see models.py)
  log    path of the Inspect log, relative to the project root

Rows labelled failed or partial are kept for the record and never analysed.
"""

from dataclasses import dataclass
from pathlib import Path

from outcome_bias.models import ORDER
from outcome_bias.paths import ROOT, RUN_INDEX


@dataclass(frozen=True)
class Run:
    label: str
    exp: str
    arm: str
    model: str
    log: str

    @property
    def path(self) -> Path:
        return ROOT / self.log


def runs() -> list[Run]:
    if not RUN_INDEX.exists():
        return []
    out = []
    for line in RUN_INDEX.read_text().splitlines():
        f = line.split("\t")
        if len(f) == 5:
            out.append(Run(*f))
    return out


def find(label=None, exp=None, arm="main", model=None) -> list[Run]:
    """Runs that finished and match every given field (None = any)."""
    return [r for r in runs()
            if r.log and r.label not in ("failed", "partial")
            and (label is None or r.label == label) and (exp is None or r.exp == exp)
            and (arm is None or r.arm == arm) and (model is None or r.model == model)]


def judged(label="run1", exp=None, arm="main", among=ORDER) -> tuple[str, ...]:
    """The models (of `among`) with a finished run matching the given fields, in reporting order."""
    have = {r.model for r in find(label, exp, arm)}
    return tuple(m for m in among if m in have)


def logs(label=None, exp=None, arm="main", model=None) -> list[Path]:
    return [r.path for r in find(label, exp, arm, model)]


def record(label: str, exp: str, arm: str, model: str, log: str) -> None:
    RUN_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with RUN_INDEX.open("a") as f:
        f.write(f"{label}\t{exp}\t{arm}\t{model}\t{log}\n")
