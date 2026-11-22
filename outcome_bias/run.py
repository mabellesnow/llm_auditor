"""Run one study on one or more models, and record each run in the run index.

  python -m outcome_bias.run <study> [--models haiku sonnet opus] [--arm main] [--label run1]
                             [--epochs N] [--batch] [--set key=value ...] [--limit N]

Examples
  python -m outcome_bias.run e3_consequences --batch                      # main arm, three Claude models
  python -m outcome_bias.run e3_consequences --models opus --label run2 --batch   # a rule 2 re-run
  python -m outcome_bias.run followup_labelled_scale --set variant=ignore --label x1-ignore --batch
  python -m outcome_bias.run e5_intent --models haiku --limit 3           # smoke test, not recorded
  python -m outcome_bias.run e3_consequences --models gemini --batch      # the three Gemini 4 models

Each model runs in turn; the chain stops at the first run that fails (for example when the API credit
runs out). A run that stops part-way is recorded as "partial". Smoke tests (--limit) go to
logs/smoke/ and are not recorded.
"""

import argparse
import os
import subprocess
import sys

from inspect_ai.log import read_eval_log

from outcome_bias import runlog
from outcome_bias.models import CLAUDE, FAMILIES, MODELS
from outcome_bias.paths import LOGS, ROOT
from outcome_bias.studies import STUDIES


def run_one(study, model_name, arm, label, epochs, batch, params, limit=None):
    model = MODELS[model_name]
    if arm not in model.arms:
        raise SystemExit(f"{model_name} has no '{arm}' arm (has: {', '.join(model.arms)})")
    cmd = [str(ROOT / ".venv" / "bin" / "inspect"), "eval", f"outcome_bias/tasks.py@{study.id}",
           "--model", model.provider_id, "-T", f"reasoning={model.arms[arm]}", "--display", "plain"]
    if epochs:
        cmd += ["-T", f"epochs={epochs}"]
    for key, value in params.items():
        cmd += ["-T", f"{key}={value}"]
    if batch:
        cmd += ["--batch=1000"]
    log_dir = LOGS / "smoke" if limit else LOGS
    if limit:
        cmd += ["--limit", str(limit)]
    cmd += ["--log-dir", str(log_dir)]
    env = dict(os.environ)
    env.pop("ANTHROPIC_BASE_URL", None)  # the Claude desktop app sets this; the API key in .env needs the default
    print(f"\n>>> {study.id} | {model_name} | arm {arm} ({model.arms[arm]}) | label {label}", flush=True)
    before = set(log_dir.glob("*.eval"))
    out = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    new = sorted((p for p in set(log_dir.glob("*.eval")) - before if _is_ours(p, study.id, model.provider_id)),
                 key=lambda p: p.stat().st_mtime)  # another run may be writing to the same folder
    if not new:  # Inspect never got as far as writing a log
        print(out.stdout[-2000:], out.stderr[-2000:], sep="\n")
        return "failed", ""
    log = str(new[-1].relative_to(ROOT))
    status = _status(ROOT / log)
    if not limit:
        runlog.record(label if status == "ok" else status, study.exp, arm, model_name, log)
    print(f"    {status}: {log}", flush=True)
    return status, log


def _is_ours(path, task, provider_id):
    try:
        e = read_eval_log(str(path), header_only=True).eval
    except Exception:  # a log another run is still writing
        return False
    return e.task == task and e.model == provider_id


def _status(path):
    log = read_eval_log(str(path))
    if log.status == "success":
        return "ok"
    scored = sum(1 for s in (log.samples or []) if s.scores)
    return "partial" if scored > 50 else "failed"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("study", choices=sorted(STUDIES))
    p.add_argument("--models", nargs="+", default=list(CLAUDE), choices=sorted(MODELS) + sorted(FAMILIES),
                   help="model names, or a family: " + ", ".join(FAMILIES) + " (default claude)")
    p.add_argument("--arm", default="main", choices=["main", "medium", "reasoning"])
    p.add_argument("--label", default="run1", help="run label in the run index (default run1)")
    p.add_argument("--epochs", type=int, default=0, help="samples per item (default: the study's)")
    p.add_argument("--batch", action="store_true", help="use the batch API (half price, slower)")
    p.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE", help="study parameters, e.g. variant=ignore")
    p.add_argument("--limit", type=int, help="smoke test: only the first N items, not recorded")
    a = p.parse_args(argv)
    study = STUDIES[a.study]
    params = dict(kv.split("=", 1) for kv in a.set)
    unknown = set(params) - set(study.params)
    if unknown:
        raise SystemExit(f"{study.id} has no parameter {sorted(unknown)} (has: {sorted(study.params) or 'none'})")
    models = [m for name in a.models for m in FAMILIES.get(name, (name,))]
    for m in models:
        status, log = run_one(study, m, a.arm, a.label, a.epochs, a.batch, params, a.limit)
        if status == "failed":
            sys.exit(f"STOPPING: {study.id} on {m} failed ({log or 'no log'})")


if __name__ == "__main__":
    main()
