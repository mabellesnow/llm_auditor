"""Read the model's reply. Every study asks for JSON: {"answer": <number>, "reason": "<one sentence>"}
(E4 adds "violations": [ticket ids]).

A reply counts as parsed only if it contains a JSON object with a numeric "answer" inside the
question's scale. Unparsed replies are excluded from the analysis, as pre-registered.
"""

import json
import re

from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState


def parse_answer(text: str) -> dict | None:
    """The last top-level JSON object in the text that has a numeric "answer" (a model sometimes corrects
    itself). Objects nested inside a parsed object are not candidates."""
    decoder = json.JSONDecoder()
    found, pos = None, 0
    for m in re.finditer(r"\{", text):
        if m.start() < pos:  # inside an object already parsed
            continue
        try:
            obj, pos = decoder.raw_decode(text, m.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("answer"), (int, float)) and not isinstance(obj.get("answer"), bool):
            found = obj
    return found


def score_reply(text: str, md: dict) -> Score:
    """Score value = the answer. Metadata: parsed, answer, json_first; for E4 also which tickets were listed.
    md is the item's metadata (lo, hi, exp; E4 also target_ticket)."""
    obj = parse_answer(text)
    if obj is None or not (md["lo"] <= obj["answer"] <= md["hi"]):  # NaN and infinities fail this too
        return Score(value=0, answer=text, metadata={"parsed": False})
    meta = {"parsed": True, "answer": float(obj["answer"]), "json_first": text.lstrip().startswith("{")}
    if md["exp"] == "e4":
        violations = obj.get("violations") or []
        if not isinstance(violations, list):  # one ticket given as a string, not a list
            violations = [violations]
        listed = [str(x).strip().upper() for x in violations]
        meta["listed"] = listed
        meta["detected"] = md["target_ticket"] in listed
        meta["others_listed"] = len([x for x in listed if x != md["target_ticket"]])
    return Score(value=float(obj["answer"]), answer=text, explanation=str(obj.get("reason", "")), metadata=meta)


@scorer(metrics=[mean()])
def answer_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        return score_reply(state.output.completion, state.metadata)

    return score
