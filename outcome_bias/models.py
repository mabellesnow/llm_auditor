"""The models, and the reasoning setting each uses in each arm.

  main       the lowest reasoning the model allows (thinking off where possible)
  medium     effort "medium" for all (E1's second arm; Sonnet did not reason at this setting)
  reasoning  the lowest effort at which the model reasons on every answer (E2, E3 second arm)

Opus 5.5 cannot switch reasoning off, so its main arm is effort "low".
Gemini 4 Hydrogen cannot either: asked for "none", it still spent 200 to 325 thinking tokens per answer in a
smoke test (22 November 2026), so its main arm is thinking level "low", as for Opus. Argon and Carbon accept
"none" and then spend no thinking tokens, so their main arm is thinking off, as for Haiku and Sonnet. Their
reasoning arm is the lowest level that thought on every smoke-test answer: "high" for Argon (about 610 thinking
tokens; none at "medium"), "medium" for Carbon (about 340; at "high" it spent about 11,000). Argon's reasoning
arm was not run: "high" is Gemini's top level, ruled out to keep reasoning effort moderate. Hydrogen, like
Opus, already reasons in its main arm, so it has no separate reasoning run.
Neon and 3.8 Flash have not been tried. Gemini 4 Argon, Carbon and Neon need a Google project with billing on;
on the free tier their quota is zero.
OpenAI entries are set up but not yet run: gpt-6-astra and gpt-6.1-sol always reason (Inspect drops
temperature for them), so their main arm is "low"; check with a one-call run before a full run.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    provider_id: str
    arms: dict
    batch_price: tuple[float, float]  # USD per million input, output tokens, batch API
    tested: bool = True


GEMINI_ARMS = {"main": "low", "medium": "medium", "reasoning": "high"}  # thinking cannot be switched off

MODELS = {
    "haiku": Model("anthropic/claude-haiku-5-5", {"main": "none", "medium": "medium", "reasoning": "high"}, (0.05, 0.25)),
    "sonnet": Model("anthropic/claude-sonnet-5-5", {"main": "none", "medium": "medium", "reasoning": "xhigh"}, (1.0, 5.0)),
    "opus": Model("anthropic/claude-opus-5-5", {"main": "low", "medium": "medium", "reasoning": "high"}, (2.0, 10.0)),
    # Google: the three Gemini 4 models pass a smoke test; Neon and 3.8 Flash have not been tried.
    # Batch is half the standard price; output includes thinking tokens.
    # Argon's and Carbon's prices double on 1 December 2026 (to 2.00, 10.00).
    "gemini-4-hydrogen": Model("google/gemini-4-hydrogen", GEMINI_ARMS, (0.75, 3.75)),
    "gemini-4-argon": Model("google/gemini-4-argon", {"main": "none", "medium": "medium", "reasoning": "high"}, (1.00, 5.00)),
    "gemini-4-carbon": Model("google/gemini-4-carbon", {"main": "none", "medium": "medium", "reasoning": "medium"}, (1.00, 5.00)),
    "gemini-4-neon": Model("google/gemini-4-neon", GEMINI_ARMS, (1.50, 7.50), tested=False),
    "gemini-3.8-flash": Model("google/gemini-3.8-flash", GEMINI_ARMS, (0.375, 1.875), tested=False),
    # Open weights, served by Ollama (OLLAMA_BASE_URL in .env); free to run, so no batch price. Its thinking
    # cannot be switched off: with no effort, "none" or think=false it still spent 280 to 435 hidden tokens on a
    # short prompt (22 November 2026), so its main arm is effort "low" (about 300 tokens per E3 answer), as for Opus.
    "inkling-2-mini": Model("ollama/inkling-2-mini", {"main": "low", "reasoning": "medium"}, (0.0, 0.0)),
    # OpenAI, not yet run
    "gpt-6-luna": Model("openai/gpt-6-luna", {"main": "none", "reasoning": "high"}, (0.05, 0.25), tested=False),
    "gpt-6.1-terra": Model("openai/gpt-6.1-terra", {"main": "none", "reasoning": "high"}, (0.50, 2.50), tested=False),
    "gpt-6.1-sol": Model("openai/gpt-6.1-sol", {"main": "low", "reasoning": "high"}, (1.00, 5.00), tested=False),
    "gpt-6-astra": Model("openai/gpt-6-astra", {"main": "low", "reasoning": "high"}, (5.00, 25.00), tested=False),
}

CLAUDE = ("haiku", "sonnet", "opus")
GEMINI = ("gemini-4-hydrogen", "gemini-4-argon", "gemini-4-carbon")  # fast, efficient frontier, most capable
OPEN = ("inkling-2-mini",)
FAMILIES = {"claude": CLAUDE, "gemini": GEMINI, "open": OPEN}
ORDER = tuple(MODELS)  # the order every analysis reports models in
SHORT_NAMES = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "gemini-4-hydrogen": "Hydrogen",
               "gemini-4-argon": "Argon", "gemini-4-carbon": "Carbon", "inkling-2-mini": "Inkling"}  # table headers


def rank(model: str) -> int:
    """Position in ORDER of a short name or a logged model name (claude-haiku-5-5 contains haiku)."""
    return next((i for i, k in enumerate(ORDER) if k in model), len(ORDER))


def ordered(names) -> tuple[str, ...]:
    """The given short model names, once each, in reporting order."""
    have = set(names)
    return tuple(m for m in ORDER if m in have)
