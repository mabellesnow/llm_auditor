"""Check the Ollama server, and whether it answers several requests at once (OLLAMA_NUM_PARALLEL).

  python -m outcome_bias.check_ollama [n_trials] [max_workers]

The server is the one Inspect uses: OLLAMA_BASE_URL in .env (for example http://<host>:11434/v1).

Times one request alone, then sends the same short prompt n_trials times from max_workers threads. A request's
time includes waiting in the server's queue, so the test compares throughput (tokens per second) instead: in
parallel it rises well above the single request's; one at a time, it stays about the same.
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from outcome_bias.models import MODELS
from outcome_bias.paths import ROOT

load_dotenv(ROOT / ".env")
if not os.environ.get("OLLAMA_BASE_URL"):
    sys.exit("Set OLLAMA_BASE_URL in .env, for example http://<host>:11434/v1")
MODEL = MODELS["inkling-2-mini"].provider_id.removeprefix("ollama/")
client = OpenAI(
    base_url=os.environ["OLLAMA_BASE_URL"],
    api_key="ollama",
    http_client=httpx.Client(trust_env=False, timeout=300),  # trust_env=False: no proxy for a local server
)

PROMPT = ('A support agent refunded £104.50 when the policy needs approval above £100. How likely is it the policy '
          'was broken, 0-100? Reply only with JSON: {"answer": <number>, "reason": "<one sentence>"}')


def run_one_trial(i):
    start = time.time()
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT}],
        extra_body={"reasoning": {"effort": "low"}},
    )
    return i, time.time() - start, r.usage.completion_tokens, r.choices[0].message.content


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    _, secs, tokens, _ = run_one_trial("alone")
    single = tokens / secs
    print(f"one request alone: {secs:.1f}s, {tokens} tokens, {single:.1f} tokens/s")
    trials = range(n)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run_one_trial, trials))
    wall = time.time() - t0
    for i, secs, tokens, text in sorted(results, key=lambda r: r[1]):
        print(f"trial {i}: done after {secs:5.1f}s  {tokens} tokens  {text[:60]!r}")
    together = sum(r[2] for r in results) / wall
    print(f"\n{n} requests from {workers} threads: wall {wall:.1f}s, {together:.1f} tokens/s "
          f"({together / single:.1f}x one request alone)")
    print("parallel" if together > 1.5 * single else "one at a time: the server is not running requests in parallel")
