"""Reading the model's reply: what counts as parsed, and what is recorded."""

from outcome_bias.scoring import parse_answer, score_reply

AGENT = {"exp": "e3", "lo": 0, "hi": 100}
E4 = {"exp": "e4", "lo": 0, "hi": 100, "target_ticket": "OPS-4105"}


def test_takes_the_last_answer_when_the_model_corrects_itself():
    assert parse_answer('{"answer": 20, "reason": "a"} No, rather: {"answer": 35, "reason": "b"}')["answer"] == 35


def test_reads_json_inside_prose_and_code_fences():
    text = 'Sure.\n```json\n{"answer": 12.5, "reason": "uses {braces} in text"}\n```'
    assert parse_answer(text) == {"answer": 12.5, "reason": "uses {braces} in text"}


def test_an_answer_nested_inside_the_reply_object_is_not_the_answer():
    assert parse_answer('{"answer": 30, "detail": {"answer": 90}}')["answer"] == 30


def test_a_malformed_object_is_skipped_for_a_later_valid_one():
    assert parse_answer('{"answer": 30, } then {"answer": 40}')["answer"] == 40


def test_needs_a_numeric_answer():
    assert parse_answer('{"answer": "high"} {"reason": "x"}') is None
    assert parse_answer('{"answer": true}') is None, "a boolean is not a number here"
    assert parse_answer("About 40.") is None


def test_an_answer_outside_the_scale_is_unparsed():
    for text in ('{"answer": 101}', '{"answer": -1}', '{"answer": NaN}', '{"answer": Infinity}'):
        s = score_reply(text, AGENT)
        assert s.metadata == {"parsed": False} and s.value == 0


def test_a_parsed_reply_records_answer_reason_and_whether_json_came_first():
    s = score_reply(' {"answer": 0, "reason": "Fine."}', AGENT)
    assert s.value == 0.0
    assert s.metadata == {"parsed": True, "answer": 0.0, "json_first": True}
    assert s.explanation == "Fine."
    assert score_reply('So: {"answer": 7}', AGENT).metadata["json_first"] is False


def test_e4_records_whether_the_target_ticket_was_listed():
    s = score_reply('{"violations": ["ops-4105 ", "OPS-4110"], "answer": 80, "reason": "r"}', E4)
    assert s.metadata["listed"] == ["OPS-4105", "OPS-4110"]
    assert s.metadata["detected"] is True
    assert s.metadata["others_listed"] == 1
    none = score_reply('{"violations": [], "answer": 10}', E4).metadata
    assert (none["detected"], none["others_listed"]) == (False, 0)


def test_e4_accepts_a_single_ticket_given_as_a_string():
    s = score_reply('{"violations": "OPS-4105", "answer": 80}', E4)
    assert s.metadata["listed"] == ["OPS-4105"] and s.metadata["detected"] is True
