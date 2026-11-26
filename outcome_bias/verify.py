"""Two checks that the stimuli are what the plans froze.

  python -m outcome_bias.verify            # both checks
  python -m outcome_bias.verify --freeze   # record the current stimulus hashes in outcome_bias/stimuli/hashes.json

1. Hashes: every file in outcome_bias/stimuli/ against outcome_bias/stimuli/hashes.json.
2. Prompts: for every finished run in the run index, rebuild each logged prompt from the current code
   and stimuli, and compare it with the prompt the model actually saw. This is the stronger check: it
   catches any change in how prompts are assembled, not just changes to the data files.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone

from inspect_ai.log import read_eval_log

from outcome_bias import runlog
from outcome_bias.paths import FREEZE, ROOT, STIMULI
from outcome_bias.studies import STUDIES

_EXP_TO_STUDY = {"e1": "e1_people", "e2": "e2_task_outcome", "e3": "e3_consequences",
                 "e4": "e4_buried_violation", "e5": "e5_intent"}
# Task names the follow-ups had before they were renamed (15 and 17 November 2026).
_OLD_TASK_NAMES = {"x1_labelled_scale": "followup_labelled_scale", "s2c_neutral_note": "followup_neutral_note",
                   "s2d_rule_purpose": "followup_rule_purpose"}


def stimulus_hashes():
    """SHA-256 of every data file in outcome_bias/stimuli/, keyed by its path inside that folder.
    The loader (__init__.py), the README and the hash record itself are not stimuli."""
    return {str(p.relative_to(STIMULI)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(STIMULI.rglob("*"))
            if p.is_file() and not p.name.startswith(".") and p.suffix not in (".md", ".py", ".pyc") and p != FREEZE}


def check_freeze(verbose=True):
    """True if every stimulus file matches outcome_bias/stimuli/hashes.json."""
    if not FREEZE.exists():
        print("NOTE: no freeze record (outcome_bias/stimuli/hashes.json).")
        return False
    frozen = json.loads(FREEZE.read_text())["files"]
    now = stimulus_hashes()
    changed = sorted(f for f in frozen if now.get(f) != frozen[f])
    added = sorted(set(now) - set(frozen))
    if verbose:
        print("Stimulus files match the freeze." if not (changed or added)
              else f"WARNING: stimuli changed since the freeze: {changed} {('new: ' + str(added)) if added else ''}")
    return not (changed or added)


def write_freeze(note):
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps({"frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "note": note, "files": stimulus_hashes()}, indent=2) + "\n")
    print(f"wrote {FREEZE.relative_to(ROOT)} ({len(stimulus_hashes())} files)")


def study_for_log(log):
    """(study id, build parameters) for a log, from its task name and arguments (old and new names)."""
    name, args = log.eval.task.split("/")[-1], log.eval.task_args or {}
    name = _OLD_TASK_NAMES.get(name, name)
    if name == "experiment":  # before the restructure: one task for E1 to E5
        params = {"n_filler": int(args.get("e4_fillers") or 24)} if args.get("exp") == "e4" else {}
        return _EXP_TO_STUDY[args.get("exp", "e1")], params
    if name == "anchored":
        return "followup_labelled_scale", {"variant": args.get("arm", "labelled")}
    if name == "e5_neutral":
        return "followup_neutral_note", {}
    if name == "purpose":
        return "followup_rule_purpose", {}
    if name in STUDIES:
        return name, {k: (int(v) if k == "n_filler" else v) for k, v in args.items() if k in STUDIES[name].params}
    return None, None


def check_prompts():
    """Rebuild every logged prompt and compare. Returns the number of mismatches."""
    total_bad = 0
    built = {}
    for run in runlog.find(arm=None):
        log = read_eval_log(str(run.path))
        study, params = study_for_log(log)
        if study is None:
            print(f"  ? {run.log}: unknown task {log.eval.task}")
            continue
        key = (study, tuple(sorted(params.items())))
        if key not in built:
            built[key] = {i.id: (i.input[0].content, i.input[1].content) for i in STUDIES[study].build(**params)}
        expected = built[key]
        seen = bad = 0
        for s in log.samples or []:
            if s.epoch != 1:
                continue
            system = next(m.content for m in s.input if m.role == "system")
            user = next(m.content for m in s.input if m.role == "user")
            seen += 1
            bad += expected.get(s.id) != (system, user)
        total_bad += bad
        print(f"  {'ok ' if not bad else 'BAD'} {run.label:<20} {run.model:<17} {run.arm:<9} {study:<23} "
              f"{seen:4d} prompts, {bad} differ")
    return total_bad


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--freeze", metavar="NOTE", help="record the current stimulus hashes, with a note saying why")
    a = p.parse_args(argv)
    if a.freeze:
        write_freeze(a.freeze)
        return
    check_freeze()
    print("Rebuilding every logged prompt from the current code:")
    bad = check_prompts()
    print("All logged prompts match." if bad == 0 else f"WARNING: {bad} logged prompts differ from the current code.")


if __name__ == "__main__":
    main()
