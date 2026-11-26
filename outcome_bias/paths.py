"""Where things live. Every other module takes its paths from here."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent

STIMULI = PACKAGE / "stimuli"  # everything the models read: transcripts, endings, questions, system prompts
FREEZE = STIMULI / "hashes.json"  # SHA-256 of every stimulus file, written when a plan is frozen

DOCS = ROOT / "docs"  # plans, results, the write-up
EXTRA_TABLES = DOCS / "3_extra_analyses" / "tables"  # tables written by the extra analyses
POST_FIGURES = DOCS / "posts" / "figures"  # figures for the blog post

LOGS = ROOT / "logs"  # Inspect logs (not in git)
RUN_INDEX = LOGS / "exp_runs.tsv"  # one row per run: label, exp, arm, model, log file
ROW_CACHE = LOGS / ".rows"  # answers already read from each log (analysis/load.py); safe to delete


def extra_table(name: str, family: str = "claude") -> Path:
    """Where an extra analysis writes table `name`: Claude's has no suffix, other families' end in _<family>.
    Creates the folder if needed."""
    EXTRA_TABLES.mkdir(parents=True, exist_ok=True)
    return EXTRA_TABLES / (f"{name}.csv" if family == "claude" else f"{name}_{family}.csv")
