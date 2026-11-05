# Installation

Run `uv sync --locked` from the repository root. This creates the project-local
environment with DuckDB, pandas, NumPy, SciPy, scikit-learn and tabulate for agent-written
analysis scripts, plus pypdfium2 and Ruff in the default development group.
Run Python scripts with `uv run <script.py>`.

Open Claude Code or Codex in this checkout. `CLAUDE.md` routes data questions to
the analysis skill; `AGENTS.md` gives Codex the same instructions. Claude Code
discovers `.claude/skills/`, and Codex discovers links to those folders under
`.agents/skills/`. No skill copying or separate installation step is needed.
Analyses use ignored `workspaces/<run>/` folders.

Configure authorized warehouse CLI/API access separately using the vendor's
instructions. See [README](README.md#use-with-an-agent) for agent usage; helper
commands and optional deliverables are described in the relevant skills.
