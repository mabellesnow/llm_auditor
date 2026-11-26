"""Every study the project has run, in one table. Each study module builds its items from outcome_bias/stimuli/.

  study id                 exp  question                                                         docs
  e1_people                e1   do these models judge people by outcomes? (positive control)     1_main_experiments
  e2_task_outcome          e2   does how the task went change how a shortcut is judged?          1_main_experiments
  e3_consequences          e3   does what the shortcut caused change it?                         1_main_experiments
  e4_buried_violation      e4   does a good-session note hide a buried violation?                1_main_experiments
  e5_intent                e5   does chance harm make an action look deliberate?                 1_main_experiments
  followup_labelled_scale  e3   is E3's verdict shift the unlabelled scale? does an instruction  1 (Haiku), 2_follow_ups
                                remove it?
  followup_neutral_note    e5   is E5's "no harm" relief the outcome, or any note?               2_follow_ups
  followup_rule_purpose    e3   does harm still move the verdict when the rule's purpose is      2_follow_ups
                                stated?

"exp" is the code written into every item's metadata and the run index (logs/exp_runs.tsv); the
analysis groups by it. Follow-up part A (the Opus re-runs) re-ran e2 and e3; it has no study of its own.
"""

from dataclasses import dataclass, field
from typing import Callable

from outcome_bias.studies import (
    e1_people,
    e2_task_outcome,
    e3_consequences,
    e4_buried_violation,
    e5_intent,
    followup_labelled_scale,
    followup_neutral_note,
    followup_rule_purpose,
)


@dataclass(frozen=True)
class Study:
    id: str
    exp: str
    build: Callable
    epochs: int  # samples per item, as pre-registered
    plan: str
    results: str
    params: dict = field(default_factory=dict)  # extra task parameters and their defaults


MAIN = ("docs/1_main_experiments/plan.md", "docs/1_main_experiments/results.md")
FOLLOW_UPS = ("docs/2_follow_ups/plan.md", "docs/2_follow_ups/results.md")

STUDIES = {
    s.id: s
    for s in [
        Study("e1_people", "e1", e1_people.build, 5, *MAIN),
        Study("e2_task_outcome", "e2", e2_task_outcome.build, 3, *MAIN),
        Study("e3_consequences", "e3", e3_consequences.build, 3, *MAIN),
        Study("e4_buried_violation", "e4", e4_buried_violation.build, 2, *MAIN, {"n_filler": e4_buried_violation.N_FILLER}),
        Study("e5_intent", "e5", e5_intent.build, 3, *MAIN),
        Study("followup_labelled_scale", "e3", followup_labelled_scale.build, 3, *FOLLOW_UPS, {"variant": "labelled"}),
        Study("followup_neutral_note", "e5", followup_neutral_note.build, 3, *FOLLOW_UPS),
        Study("followup_rule_purpose", "e3", followup_rule_purpose.build, 3, *FOLLOW_UPS),
    ]
}
