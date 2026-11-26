"""The run index, the model table, the Inspect tasks, and how verify maps old logs to studies."""

from types import SimpleNamespace

import pytest

from outcome_bias import runlog, tasks
from outcome_bias.models import CLAUDE, FAMILIES, MODELS, ORDER, ordered, rank
from outcome_bias.studies import STUDIES
from outcome_bias.verify import study_for_log


@pytest.fixture
def index(tmp_path, monkeypatch):
    path = tmp_path / "exp_runs.tsv"
    monkeypatch.setattr(runlog, "RUN_INDEX", path)
    return path


def test_record_then_find(index):
    runlog.record("run1", "e3", "main", "sonnet", "logs/b.eval")
    runlog.record("run1", "e3", "main", "haiku", "logs/a.eval")
    runlog.record("failed", "e3", "main", "opus", "logs/c.eval")
    runlog.record("run1", "e3", "reasoning", "haiku", "logs/d.eval")
    assert [r.log for r in runlog.find(label="run1", exp="e3")] == ["logs/b.eval", "logs/a.eval"]
    assert runlog.judged(exp="e3") == ("haiku", "sonnet"), "reporting order, not index order"
    assert len(runlog.find(arm=None)) == 3, "failed runs are never analysed"


def test_a_failed_run_without_a_log_is_kept_but_never_found(index):
    index.write_text("failed\te5\tmain\thaiku\t\n")
    assert len(runlog.runs()) == 1 and runlog.find(arm=None) == []


def test_a_malformed_row_is_an_error_not_a_silently_missing_run(index):
    index.write_text("run1\te3\tmain\thaiku\tlogs/a.eval\nrun1 e3 main sonnet logs/b.eval\n\n")
    with pytest.raises(ValueError, match="line 2"):
        runlog.runs()


def test_a_missing_index_means_no_runs(index):
    assert runlog.runs() == []


def test_model_table():
    assert all("main" in m.arms for m in MODELS.values())
    assert set(FAMILIES["claude"]) == set(CLAUDE)
    assert all(set(f) <= set(MODELS) for f in FAMILIES.values())
    assert ORDER == tuple(MODELS)


def test_rank_and_ordered_follow_the_model_table():
    assert rank("claude-haiku-5-5") < rank("claude-opus-5-5") < rank("gemini-4-carbon") < rank("unknown")
    assert rank("unknown") == len(ORDER), "a logged model name not in the table sorts last"
    assert rank("opus") == ORDER.index("opus")
    assert ordered({"inkling-2-mini", "opus", "haiku"}) == ("haiku", "opus", "inkling-2-mini")


def test_task_filters_and_reasoning_off():
    t = tasks.make_task("e3_consequences", epochs=None, reasoning="none", conditions="harm, payoff",
                        questions=["violation", "blame"])
    md = [s.metadata for s in t.dataset]
    assert {m["cond"] for m in md} == {"harm", "payoff"} and {m["question"] for m in md} == {"violation", "blame"}
    assert t.epochs == STUDIES["e3_consequences"].epochs
    assert (t.config.temperature, t.config.max_tokens, t.config.reasoning_effort) == (1.0, 1500, "none")


def test_task_with_reasoning_on_leaves_temperature_to_the_provider():
    t = tasks.make_task("e1_people", epochs=2, reasoning="low")
    assert (t.config.temperature, t.config.max_tokens, t.epochs) == (None, None, 2)


def log(task, **args):
    return SimpleNamespace(eval=SimpleNamespace(task=task, task_args=args))


@pytest.mark.parametrize("task, args, expected", [
    ("experiment", {"exp": "e3"}, ("e3_consequences", {})),
    ("experiment", {"exp": "e4", "e4_fillers": "18"}, ("e4_buried_violation", {"n_filler": 18})),
    ("anchored", {"arm": "ignore"}, ("followup_labelled_scale", {"variant": "ignore"})),
    ("x1_labelled_scale", {"variant": "labelled"}, ("followup_labelled_scale", {"variant": "labelled"})),
    ("e5_neutral", {}, ("followup_neutral_note", {})),
    ("s2d_rule_purpose", {}, ("followup_rule_purpose", {})),
    ("outcome_bias/e4_buried_violation", {"n_filler": "24", "reasoning": "none"},
     ("e4_buried_violation", {"n_filler": 24})),
    ("something_else", {}, (None, None)),
])
def test_verify_maps_every_task_name_ever_logged(task, args, expected):
    assert study_for_log(log(task, **args)) == expected
