# HAL Light

For any empirical/data question asked in this repo, use the `analyse` skill
(`.claude/skills/analyse/SKILL.md`) — it defines the workspace, deliverables, rigor
rules, and reference-material pointers. `INSTALLATION.md` has the warehouse access
mechanics.

Hard constraints: a run writes only inside its own `workspaces/<run>/` folder; fully
qualified table names in all SQL (absolute file paths when querying local files);
aggregates only in the conversation and deliverables — raw rows never surface, and
row-level work runs only through the skill's sanctioned routes (in-warehouse compute,
quarantine sub-run, explicit per-run opt-in extract); repo/skill edits happen only on
explicit user request.
