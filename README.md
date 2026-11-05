# HAL Light

HAL Light is a set of skills and Python helpers for Claude Code and Codex that turns ad-hoc data questions into reproducible HTML briefs.

Left to themselves, coding agents can write SQL and Python, follow leads, and summarize results—but their work usually lives and dies in the chat transcript. HAL Light leaves the analytical choices to the model while enforcing a strict bar for what "done" looks like: a defensible comparison, saved queries someone else can rerun, and a self-contained report that states what would change the conclusion.

Use it when you have a coding agent, access to data, and a question where the answer will be scrutinized—like explaining a metric movement, isolating drivers, or making a recommendation. No external service or custom engine is required.

## How it works

HAL Light runs inside your existing agent environment using three skills (`analyse`, `dataviz`, and `live-prep`) plus local Python utilities for SVG chart rendering, palette checks, and HTML linting. 

Instead of locking the agent into rigid code contracts, the skills set rules for how the agent conducts and documents its work:

* **Challenge the comparison first.** Before computing headline numbers, the agent has to define the estimand, population, and baseline. It looks for the strongest alternative framing and tests it. If a comparison is confounded, it is instructed to normalize rates, align time periods, or compare equivalent cohorts rather than reporting raw differences.
* **Try to break the recommendation.** Before recommending an action, the agent runs the check most likely to reverse its conclusion. If key data is missing, the recommendation is marked conditional in the summary. For driver analyses, it has to check obvious cuts and material unexplained gaps before writing them off as open questions.
* **Keep every number reproducible.** Every reported figure must come from a saved query or script executed during the run (external context is cited and labeled separately). Headline numbers are recomputed independently, decompositions must reconcile to totals, and failed queries are logged as gaps rather than treated as zero.
* **Leave an audit trail.** A finished analysis has to be reviewable without reading the chat history. The agent logs its decisions as it goes, records filters and limitations, and saves all working scripts.

The `analyse` skill consults short [analytical references](.claude/skills/analyse/references/) when relevant: comparison baselines, event dates and conversion maturity, causal attribution, and decomposition interpretation. As evidence changes the investigation, the agent can revise its framing and consult newly relevant guidance while preserving the user's intended question. These references help identify misleading comparisons and explanations; method selection remains open.

Note that these are prompt-level instructions, not hard programmatic guardrails. The HTML linter catches broken formatting and missing elements, but you still need to review the agent's methodology and SQL.

## What it produces

Simple one-number questions can stay in chat. For deeper work, HAL Light writes everything to a dedicated folder per run (`workspaces/<date>-<question>/`, git-ignored by default):

```text
brief.html       Self-contained report (findings, SVG charts, tables, caveats)
prompt.md        Your original question and follow-up requests
methodology.md   Population definitions, filters, methods, and limitations
run_log.md       Step-by-step decisions and validation checks from the run
scratch/         Saved SQL, Python scripts, intermediate data, and chart specs
```

`brief.html` puts the conclusion up front, followed by supporting evidence, charts, and data tables (every charted value is also rendered in a table). Because it's a single HTML file with inline SVG, you can share it directly without hosting anything. Ask follow-up questions in the same session and the agent will update `brief.html` and append to the logs.

If you need to present the findings live, the optional **live-prep** skill generates private speaker notes from the finished analysis. It flags likely pushback, key assumptions, and next steps, separating what is directly backed by the data from what requires deeper methodological caveats.

## Examples

* **[Telecom churn and retention targeting](examples/iranian-telecom-churn-local/workspace/brief.md)** · [question](examples/iranian-telecom-churn-local/question/BRIEF.md) · [full workspace](examples/iranian-telecom-churn-local/workspace/).
* **[Seoul bike-sharing demand and fleet planning](examples/seoul-bike-sharing-demand/workspace/brief.md)** · [question](examples/seoul-bike-sharing-demand/question/BRIEF.md) · [full workspace](examples/seoul-bike-sharing-demand/workspace/).

The Markdown editions include the full report text, charts, and tables and render directly on GitHub. For the original report layout, download a `brief.html` file and open it in your browser. These Markdown copies are provided for the examples; the analysis skill's standard deliverable remains `brief.html`.

## Why "Light"?

Earlier iterations [architecture and trade-offs](design/architecture.md) enforced the analytical workflow through strict code contracts and an orchestration engine. In practice, that rigidity restricted what the agent could explore more than it improved accuracy. As frontier models got better at reasoning, giving the agent open-ended tool use with clear methodological rules worked better than a rigid pipeline.


## Setup and usage

Requires Python 3.12+ and `uv`:

```sh
git clone https://github.com/bmalthi/hal-light.git
cd hal-light
uv sync --locked
```

Open the repo in **Claude Code** (which reads `.claude/skills/`) or **Codex** (which reads `.agents/skills/` and `AGENTS.md`). For other agents, point them directly to `.claude/skills/analyse/SKILL.md`. See [INSTALLATION.md](INSTALLATION.md) for details.

To run an analysis against local files or links:

> Use hal-analyse to answer [your question]. The data is at [link or local file path].

To let the agent query your warehouse directly (using whatever tools and credentials your agent already has configured):

> Use hal-analyse to investigate [your question]. Use [warehouse connection or query tool] to pull the data.

In Codex, you can also invoke `$analyse`, `$dataviz`, or `$live-prep` directly.

## Repository layout

| Path | Contents |
| --- | --- |
| `.claude/skills/` | `analyse`, `dataviz`, and `live-prep` skills, HTML templates, and Python helpers |
| `.claude/skills/analyse/references/` | Focused analytical guidance, consulted as the question and investigation require |
| `.agents/skills/` | Symlinks for Codex skill discovery |
| `design/` | [How HAL became Light](design/architecture.md) (architecture and trade-offs) |
| `tests/` | Offline behavior and security regression tests |
| `examples/` | Example questions, datasets, and committed analysis workspaces |

`CLAUDE.md` routes analysis requests; `AGENTS.md` points to it; `pyproject.toml` and `uv.lock` define the environment. Generated output and personal Claude settings are git-ignored. See [CHANGELOG.md](CHANGELOG.md) for release notes and [NOTICE](NOTICE) for attributions.

Root `workspaces/` stays git-ignored; analysis workspaces under `examples/` are committed.

## License

[Apache-2.0](LICENSE) for original HAL Light material. Copyright 2026 bmalthi. Adapted Anthropic dataviz material is excluded; see [NOTICE](NOTICE).
