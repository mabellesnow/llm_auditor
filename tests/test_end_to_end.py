"""A whole run on Inspect's mock model, with no API calls: task, scorer, log, rows, contrast."""

import pytest
from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelOutput, get_model

from outcome_bias import paths, tasks
from outcome_bias.analysis import load
from outcome_bias.stats import contrast, unit_means


def mock_run(tmp_path, reply, limit=None):
    """E3's violation question (120 items, or the first `limit`) answered with the same reply every time."""
    task = tasks.make_task("e3_consequences", epochs=1, reasoning="none", questions="violation")
    outputs = [ModelOutput.from_content(model="mockllm/model", content=reply) for _ in range(limit or 120)]
    [log] = inspect_eval(task, model=get_model("mockllm/model", custom_outputs=outputs), log_dir=str(tmp_path / "logs"),
                         display="none", limit=limit)
    assert log.status == "success"
    return log.location


@pytest.fixture
def row_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "ROW_CACHE", tmp_path / "rows")
    load._load_one.cache_clear()
    yield paths.ROW_CACHE
    load._load_one.cache_clear()


def test_parsed_answers_reach_the_analysis_and_are_cached(tmp_path, row_cache):
    path = mock_run(tmp_path, '{"answer": 40, "reason": "Looks fine."}')
    rows, bad = load.load([path])
    assert (len(rows), bad) == (120, 0)
    r = rows[0]
    assert (r["question"], r["answer"], r["reason"], r["model"], r["epoch"]) == ("violation", 40.0, "Looks fine.",
                                                                               "model", 1)
    c = contrast(unit_means(load.select(rows, "violation", "borderline")), "harm", "omitted")
    assert c[:3] == (0, 0, 0) and c[5] == 21

    [cached] = row_cache.glob("*.json")
    load._load_one.cache_clear()
    assert load.load([path]) == (rows, bad), "rows read back from the cache must equal rows read from the log"
    assert list(row_cache.glob("*.json")) == [cached]


def test_unparsed_answers_are_counted_and_left_out(tmp_path, row_cache):
    rows, bad = load.load([mock_run(tmp_path, "I would say about forty.", limit=5)])
    assert (rows, bad) == ([], 5)
