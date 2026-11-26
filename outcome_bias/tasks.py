"""Inspect entry points: one task per study. Usually started through the runner:

  python -m outcome_bias.run e3_consequences --models haiku sonnet opus --batch

or directly:

  inspect eval outcome_bias/tasks.py@e3_consequences --model anthropic/claude-haiku-5-5 -T reasoning=none

Task parameters (all tasks):
  epochs      samples per item (default: as pre-registered for the study)
  reasoning   reasoning effort; "none" switches thinking off and fixes temperature 1
  conditions  keep only these endings, comma-separated (for baseline-only pilots)
  questions   keep only these questions, comma-separated (for slow models; prompts are unchanged)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # see README: macOS hides the .pth file

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import generate

from outcome_bias.scoring import answer_scorer
from outcome_bias.studies import STUDIES


def _names(value) -> set[str]:
    """A comma-separated string or a list (inspect -T turns a,b,c into a list)."""
    parts = value if isinstance(value, (list, tuple)) else str(value).split(",")
    return {str(x).strip() for x in parts}


def make_task(study_id: str, epochs: int | None, reasoning: str, conditions: str = "", questions: str = "",
              **params) -> Task:
    study = STUDIES[study_id]
    items = study.build(**params)
    if conditions:
        keep = _names(conditions)
        items = [i for i in items if i.metadata["cond"] in keep]
    if questions:
        keep_q = _names(questions)
        items = [i for i in items if i.metadata["question"] in keep_q]
    off = reasoning == "none"
    return Task(
        dataset=MemoryDataset(items),
        solver=[generate()],
        scorer=answer_scorer(),
        epochs=epochs or study.epochs,
        config=GenerateConfig(reasoning_effort=reasoning, temperature=1.0 if off else None,
                              max_tokens=1500 if off else None),
    )


@task
def e1_people(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("e1_people", epochs, reasoning, conditions, questions=questions)


@task
def e2_task_outcome(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("e2_task_outcome", epochs, reasoning, conditions, questions=questions)


@task
def e3_consequences(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("e3_consequences", epochs, reasoning, conditions, questions=questions)


@task
def e4_buried_violation(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = "", n_filler: int = 24):
    return make_task("e4_buried_violation", epochs, reasoning, conditions, questions=questions, n_filler=n_filler)


@task
def e5_intent(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("e5_intent", epochs, reasoning, conditions, questions=questions)


@task
def followup_labelled_scale(variant: str = "labelled", epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("followup_labelled_scale", epochs, reasoning, conditions, questions=questions, variant=variant)


@task
def followup_neutral_note(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("followup_neutral_note", epochs, reasoning, conditions, questions=questions)


@task
def followup_rule_purpose(epochs: int = 0, reasoning: str = "none", conditions: str = "", questions: str = ""):
    return make_task("followup_rule_purpose", epochs, reasoning, conditions, questions=questions)
