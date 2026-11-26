"""What the models see. The digests pin every prompt of every study: a failure here means a logged run could no
longer be rebuilt (python -m outcome_bias.verify checks the same thing against the logs themselves)."""

import hashlib
import json
import random

import pytest

from outcome_bias import stimuli
from outcome_bias.prompts import _renumber, agent_transcript, ask, e4_session, follow_up
from outcome_bias.studies import STUDIES
from outcome_bias.verify import check_freeze

# (study id, build parameters): (number of items, first 16 hex digits of the SHA-256 over every item)
DIGESTS = {
    ("e1_people", ()): (180, "96da3dfa01e83a4e"),
    ("e2_task_outcome", ()): (858, "59ca6868ecc2439a"),
    ("e3_consequences", ()): (840, "348cb39a77e5580f"),
    ("e4_buried_violation", ()): (180, "620269254641efca"),
    ("e5_intent", ()): (180, "9bc599356f7eafc4"),
    ("followup_labelled_scale", (("variant", "labelled"),)): (120, "57b602399a0e1a85"),
    ("followup_labelled_scale", (("variant", "ignore"),)): (120, "c2645dbdb340602e"),
    ("followup_neutral_note", ()): (252, "bc3d282d1af0d235"),
    ("followup_rule_purpose", ()): (420, "50e43d87115dab9a"),
}


def digest(items):
    h = hashlib.sha256()
    for i in items:
        h.update(json.dumps([i.id, i.input[0].content, i.input[1].content, i.metadata], sort_keys=True,
                            default=str).encode())
    return h.hexdigest()[:16]


def test_stimuli_match_the_freeze():
    assert check_freeze(verbose=False), "a stimulus file changed since the freeze: see python -m outcome_bias.verify"


def test_every_study_has_a_digest():
    assert {sid for sid, _ in DIGESTS} == set(STUDIES)


@pytest.mark.parametrize("key", DIGESTS, ids=lambda k: "-".join([k[0], *(v for _, v in k[1])]))
def test_prompts_are_unchanged(key):
    study, params = key
    items = STUDIES[study].build(**dict(params))
    n, expected = DIGESTS[key]
    assert len(items) == n
    assert digest(items) == expected, f"{study}: prompts changed; every logged run of it would stop rebuilding"


@pytest.mark.parametrize("study", STUDIES)
def test_items_are_well_formed(study):
    items = STUDIES[study].build()
    assert len({i.id for i in items}) == len(items), "sample ids must be unique: the analysis and verify key on them"
    for i in items:
        md = i.metadata
        assert md["exp"] == STUDIES[study].exp
        assert md["lo"] < md["hi"]
        assert [m.role for m in i.input] == ["system", "user"]
        assert i.input[1].content.count("\n\nQUESTION: ") == (0 if md["exp"] == "e4" else 1)


def test_ask_and_follow_up():
    assert ask("BODY", "Q?") == "BODY\n\nQUESTION: Q?"
    assert follow_up("It worked.") == "FOLLOW-UP NOTE: It worked."


def test_agent_transcript_layout():
    s = stimuli.agent_scenarios()[0]
    text = agent_transcript(s, follows_rule=False, ending="FOLLOW-UP NOTE: x", policy_note="Why: y")
    assert text.startswith(f"POLICY:\n{s.policy}\nWhy: y\n\nTRANSCRIPT:\nUSER: {s.task}\n")
    assert text.endswith("\nFOLLOW-UP NOTE: x")
    assert agent_transcript(s, False, None).endswith(s.wrapup[-1])


def test_the_two_versions_differ_only_in_the_middle():
    s = stimuli.agent_scenarios()[0]
    bent, kept = s.steps(False), s.steps(True)
    assert bent[:len(s.context)] == kept[:len(s.context)] == s.context
    assert bent[-len(s.wrapup):] == kept[-len(s.wrapup):] == s.wrapup


def test_e4_session_is_seeded_and_the_target_sits_in_the_middle_third():
    target, fillers = stimuli.e4_targets()[0], stimuli.e4_fillers()
    violating, tid, ids = e4_session(target, True, 1, fillers, 24)
    compliant, tid2, ids2 = e4_session(target, False, 1, fillers, 24)
    assert (tid, ids) == (tid2, ids2), "the same seed must give the same session for both versions"
    assert len(ids) == 25 and len(set(ids)) == 25
    assert 25 // 3 <= ids.index(tid) <= 2 * 25 // 3
    assert violating != compliant
    assert e4_session(target, True, 1, fillers, 24) == (violating, tid, ids)
    assert e4_session(target, True, 2, fillers, 24)[0] != violating


def test_e4_session_reuses_routine_tickets_with_fresh_numbers():
    target, fillers = stimuli.e4_targets()[0], stimuli.e4_fillers()
    _, _, ids = e4_session(target, True, 1, fillers, len(fillers) + 10)
    assert len(ids) == len(fillers) + 11


def test_renumber_shifts_reference_numbers_only():
    out = _renumber(["refund C-1234 on claim='E-5678'", "no ids here", "job 4321 for id=42"], random.Random(0))
    assert out[1] == "no ids here"
    assert "C-1234" not in out[0] and "claim='E-5678'" not in out[0]
    assert out[2].startswith("job ") and "job 4321" not in out[2]
    assert out[2].endswith("id=42"), "numbers under three digits are left alone"
