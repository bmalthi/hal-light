---
name: analyse
description: >
  Run a data analysis from first principles — query your data warehouse directly, work
  in an isolated run workspace, and ship a self-contained brief.html plus a run log and
  methodology summary. Use for any empirical or data question asked in this repo:
  business metrics, movements, drivers, comparisons, deep dives, or quick pulls.
---

# analyse — a light harness over the raw model

You are the analyst. This skill does not tell you how to analyze — it sets the output
discipline (what a run leaves behind), points you at the reference material, and names
a few rigor rules. Everything else — framing, cuts, interpretation, judgment — is yours.

## Match the depth to the ask

Judge the ask before standing anything up:

- **Trivial pull** — one number, one aggregate ("volume last week", "how many X"). Query,
  answer in chat, done. No workspace, no brief.
- **Real analysis** — a comparison, a trend, a "why"/driver question, anything someone
  will act on or forward. Full workspace and deliverables below.

When unsure, take the deeper route. Say which you took, so the user can ask for more or
less. Pure definitional questions ("what does conversion rate mean?") need no data at all — answer
from the reference material.

## Workspace

Every real run gets its own folder:

```
workspaces/<YYYY-MM-DD>-<slug>/
  prompt.md        # the ask, verbatim, plus every later user steer — appended as dated entries
  run_log.md       # append-only decision trail, written as you go
  methodology.md   # closing summary of how the answer was computed
  brief.html       # the final answer — self-contained single-page HTML (document brief)
  brief.md         # optional: Marp source, only if a slide deck was requested
  scratch/         # ALL working files — SQL, python/other helper scripts, pulled aggregates, temp/intermediate data, chart specs/SVGs
```

- `<slug>` is short kebab-case from the question. If the path exists, suffix `-2`, `-3`, … —
  **never overwrite a prior run's folder.**
- **Root stays clean:** only the named deliverables (`prompt.md`, `run_log.md`,
  `methodology.md`, `brief.html`, optional `brief.md`) live at the run root. Every other
  file the run produces — python or shell helper scripts, SQL, pulled data files,
  intermediate outputs, chart working files — is written to `scratch/`, never to the run
  root and never to the repo root.
- **`brief.html` is always the canonical, current answer.** When steers force a rebuild,
  update it in place — never fork `brief_v2.html` / `brief_final.html` at the root. Drafts
  and superseded versions live in `scratch/` or are deleted; a reader opening `brief.html`
  must never find a stale variant. Extra deliverables the user explicitly asks for (a
  talking track, a methods explainer, a deck alongside the document) may also sit at the
  root — name each in `run_log.md` and `methodology.md` so the folder stays legible.
- **Isolation:** run artifacts stay in their own folder; explicitly authorized input files may be read. Never read or reuse another
  run's outputs unless the user explicitly asks. Never write outside `workspaces/<this-run>/`
  during a run — repo/skill edits happen only on explicit user request.
- `workspaces/` is gitignored: run artifacts, not repo content.

**Sub-run mode.** When invoked by a parent run on a sub-question, the caller supplies
the workspace root — `workspaces/<parent-run>/analyse/<sub-slug>/` — with `prompt.md`
already written. Don't create a new top-level run folder; work inside the given
subfolder under the same contract (own `run_log.md`, `scratch/`, `methodology.md`). If
the caller asked for a findings summary rather than a full brief, close with the
summary in `run_log.md` and skip `brief.html`. "Own folder" for isolation purposes
means that subfolder; the parent run reads your outputs, you read only its handoff in
`prompt.md`.

**Delegate your own deep dives.** The same mechanism runs downward from any `analyse`
run, and taking it is encouraged: when a separable sub-question emerges mid-run that
deserves its own open-ended dig — its own hypothesis space, its own population, or
enough pulls to crowd this run's log — spawn a fresh-context `analyse` subagent in
`<this-run>/analyse/<sub-slug>/`: write its `prompt.md` handoff (the sub-question, the
context it needs, and whether you want a full brief or just a findings summary), run it
in sub-run mode, and consume its conclusion as an instrument in your `run_log.md`.
Prefer delegating over inflating the parent run; keep single confirming pulls inline.

**Share inputs within a run.** Include the applicable population, periods, metric
definitions, and reusable base aggregates with their instrument pointers in each
sub-run's `prompt.md` handoff. Reuse a pull when its population, dates, grain, and
metric match; query again when the sub-question needs something different. A child
may challenge the inherited frame: return the revised definition and reason so the
parent can reconcile the findings before combining them.

**Quarantine sub-run for unstructured text.** Reading free-text records — tickets,
survey verbatims, error messages, feedback — is the one analysis that cannot run on
aggregates: the reading *is* the analysis. Route it through a dedicated sub-run. The
subagent queries the text sample and reads it in its own context only; what crosses
back is exclusively aggregate — theme labels with counts, category prevalences,
categorical characterizations. No verbatim quotes, no identifiers, and no row-level
data written to any file: rows may pass through the subagent context (subject to the host and provider retention settings),
never into `prompt.md` handoffs, logs, scratch files, or the parent conversation.
Every theme returns with a count attached and the parent logs the summary as an
instrument like any other — a theme without a prevalence number is an anecdote, not
a finding.

## Deliverables

**`prompt.md`** — the user's original question verbatim, written at run start. When the
user steers mid-run ("also cut it by channel", "ignore the pilot group", "focus on last month"),
append each steer as a dated entry. The file is the honest record of what was asked.
Omit credentials from saved requests and logs.

**`run_log.md`** — an append-only log, written *as decisions are made*, never
reconstructed after the fact. It opens with the framing contract (see Rigor).
Short dated bullets: the decision, its reason, and — for
any load-bearing number — its instrument (table, filters, weight/metric expression, and
the `scratch/` SQL file or script that produced it). Timestamps come from actually running
`date -u +%Y-%m-%dT%H:%M:%SZ`, never invented or reused. Record user steers, corrections,
ruled-out branches, and anything left open. Prose and narrative belong in the brief; the
log keeps verdicts and pointers.

**`methodology.md`** — written once at the end: data sources and tables used (fully
qualified), the population and filters, how each headline number was computed, key
analytical choices and why, and what was checked. A reader should be able to reproduce
the answer from this file plus `scratch/` without replaying the session.

**`brief.html`** — the answer, **a single-page document brief** (the **default**
deliverable; a slide deck is an opt-in variant, below). Compose it when the analysis
settles; if later steers change the answer, revise it in place:

- **Start from the shell**: copy `.claude/skills/analyse/assets/brief_template.html`
  into the run folder and fill it — don't hand-roll the CSS. Cut sections that don't
  apply; never ship placeholders.
- **Self-contained**: inline CSS, no JS, no external fonts/scripts/network — it must
  render anywhere as one file. Charts, if any, are inline SVG; consult the `dataviz`
  skill (in this repo, `.claude/skills/dataviz/`) before charting, and make sure every
  charted number is also in a table (no hover in a static file). Render charts pinned
  to light (`render.py --single-mode light`) — the template is light-scheme only, and a
  default render carries a `prefers-color-scheme` block that flips the chart dark on
  the white page for dark-mode viewers.
- **Presentation variant (optional)** — only when the ask specifically calls for
  slides / a deck / a presentation. Author a Marp deck instead of (or alongside) the
  document: `brief.md` with `marp: true` and one slide per `---`, exported via
  `marp brief.md -o brief.html --html`. Set `* { box-sizing: border-box }` so section
  padding holds, inline the chart SVGs at build time, and QA each slide. **Default to the
  document brief** unless a presentation is requested.
- **Executive summary first**: 1–3 plain-language sentences at the top for a reader who
  reads nothing else — what happened, why, whether anyone needs to act. No jargon.
- **The brief is the answer and its support — not a process doc.** An exec-ready
  narrative of what we found and why: the finding, the evidence that carries it
  (key numbers, tables, charts, decompositions), the uncertainty, and what to do.
  Full support belongs in the brief — don't strip it to a bare answer. And answer
  the *whole* question as asked: if the ask is "why does observed look better/worse
  than expected", the brief must bridge observed to expected (the masking/driver
  story), not just publish the counterfactual estimate the cleanest method
  identifies. A finding the reader will distrust ("X reads flat but everyone
  expects it negative") gets reconciled head-on — lay out the competing reads and
  why they differ — rather than asserted. What doesn't
  belong is the session's own history: write for a reader who never saw an earlier
  draft, as if this were the only analysis ever produced. No revision narration —
  "corrected", "now includes", "the metric now matches", retiring/superseding an
  in-session estimate, contrasting against an earlier version's numbers, or rebutting
  hypotheses the audience never held. Mid-run corrections simply yield the right
  number; how it got right lives in `run_log.md` and `methodology.md`. Section
  headings state conclusions about the business, not about the analysis ("most of
  the loss occurs before onboarding", not "the funnel now includes the missing
  upstream loss"). One exception: if a figure the audience already received
  *outside this run* is being revised, say so in one line — because the reader
  holds the old number, not because the run did.
- **Then the findings**, each with its key number inline; keep tables for segment-level
  results.
- **Caveats as watch-items**: frame each as "what would change the call", not as an
  apology. Don't bury the answer in hedges.
- **End with Question & Framing**: close the brief with the ask as asked (from
  `prompt.md`), how the period/metrics/deliverable were resolved, and any steers that
  changed scope (new cuts, changed metric, narrowed window) — so the brief documents
  what was asked without the run folder. State the underlying analytical question, not
  the session mechanics ("what is the impact of X on Y", not "redo the analysis and fix
  the review findings"); corrections of the run's own missteps are run-log material,
  not brief content. The template has the block.
- **Coverage check before shipping**: re-read `prompt.md` — the ask plus every steer —
  and confirm the brief answers each part: every requested cut, metric, and composite.
  If the ask names a composite, the brief must deliver the composite, not just its
  components. Work computed but never assembled into the deliverable is a miss, not
  a draft. Log the check in `run_log.md` — one line mapping each ask-part to where
  the brief answers it is enough. (In sub-run mode, run the same check against the
  closing summary.)
- **Static check before shipping**:
  `uv run .claude/skills/analyse/scripts/verify_brief.py <run>/brief.html` — fails on
  placeholders, leftover template markers, missing structure, external assets, and JS;
  warns on the rest (`--strict` promotes warnings). Skill scripts are stdlib-only, so
  use `uv run` for these helpers as well as analysis code.
- **No PDF by default**: `brief.html` is the deliverable. Do not render or log a skipped
  PDF unless the user explicitly asks for one; if they do, render with headless Chrome
  (`--headless --print-to-pdf=... file://...brief.html`) — never an HTML→PDF converter.
- **If you built the optional Marp deck**: verify it with `verify_brief.py --deck`
  (allows Marp's own script tags; placeholder and external-asset checks still apply);
  QA each slide by rasterizing it —
  sections are a fixed 1280×720 and overflowing content is the usual defect. With no
  browser for `marp --images`, use macOS `qlmanage` on the `--template bare` output plus
  a `section { zoom: … }` shim (Quick Look previews the deck at a sub-1280 viewport and
  otherwise crops the right edge). PDF: `marp brief.md -o brief.pdf`.

**`live_prep.md`** — optional, on explicit request only: when the user will present
or defend the brief live, the `live-prep` skill (in this repo,
`.claude/skills/live-prep/`) produces `workspaces/<run>/live_prep.md`, the
presenter's private defense doc — anticipated questions, calibrated confidence,
hard choices with "if wrong" lines. It projects from the shipped brief, `run_log.md`,
and `methodology.md`, so draft it after the coverage and static checks pass. It is
presenter-only — never shipped to the audience — and is logged as an extra
deliverable per the clean-root rule.

## Analyst posture

- **Measure from the data; don't theorize from prior knowledge.** Every claim in the
  brief traces to a number computed this run. External figures enter only through
  the fetched-context channel (see Rigor) — as framing, never as claims.
- **Lead with the answer, then qualify it.**
- **Run the obvious next cut.** For driver/"why" questions, frame the main decomposition
  axes (time, segment/mix, denominator, channel, cohort, calendar shock) and actually run
  the cuts that could change the answer — don't list them as "next steps". Leave a
  residual open only after the obvious cuts are run or the data genuinely isn't there.
- **A confounded comparison gets a better cut** — a rate, common support, a stratified or
  event-time view — not just a "could be confounded" caveat.
- **Aggregates, not rows.** No record-level data ever enters the conversation or the
  deliverables — that line is absolute. Row-level *compute* is a different matter:
  SQL that scans, joins, or windows over raw rows inside the warehouse is always
  fine — the rule governs what comes back, not what the query touches. If you need
  more detail, aggregate finer; describe tiny slices categorically rather than in
  ways that single out a record. Two sanctioned routes exist for work that genuinely
  needs rows — the quarantine sub-run for unstructured text (see Sub-run mode) and
  the opt-in row-level extract (see Rigor). Neither moves the line above.

## Rigor

### Targeted analytical guidance

Consult the relevant references as the investigation develops, starting during
framing. Route by what you are currently trying to establish, including questions
discovered mid-run. New evidence may change the working question, population,
comparison, or method: revise the framing and consult any newly relevant guidance
before relying on the revised analysis. Preserve the user's intended question and
decision; explain when the revised analysis can answer only part of it. Use references
already read without rereading unless needed.
Paths below are relative to this skill directory.

| Read when… | Reference | Usually unnecessary for… |
|---|---|---|
| Interpreting a difference between time periods—its size, direction, significance, or drivers | [Comparison baselines](references/comparison-baselines.md) | A single-period lookup or a series presented without interpreting a change |
| The answer depends on which event defines the period, conversion maturity, or differences in time to an outcome | [Dates and cohorts](references/dates-and-cohorts.md) | Counts by one unambiguous event date with no delayed outcome |
| Answering “why,” identifying drivers, or using an explanation to justify a recommendation | [Attribution](references/attribution.md) | Describing a level, trend, or composition without explaining its cause |
| Assigning portions of a difference to components, such as mix versus within-group change or volume versus price | [Decomposition interpretation](references/decomposition-interpretation.md) | A simple breakdown of a total into categories |

These references help apply the rigor obligations below; they do not prescribe a
method or a fixed sequence. Start with the smallest check that can expose a material
problem, reuse relevant work already done, and deepen the investigation when the
result could change the answer. Record material choices in the existing run log and
methodology; no separate reference checklist is needed. Trivial lookups retain the
lightweight path above.

### Standing obligations

- **Write the framing contract before the first load-bearing query** (real runs only —
  a trivial pull answers in chat and skips this; schema and scoping peeks may precede
  the contract, but no number that could reach the brief). Open the run log with a
  short block naming: the **estimand** (the precise quantity that answers the ask),
  the **population** (who/what is in and out), the **comparison design** (the control,
  baseline, or counterfactual — and why it isolates the effect from the obvious
  confounders), and the **decision surface** (the exact final output the reader asked
  for — if the ask is a composite, name every component *and* the composite). Then
  challenge the frame once: state the strongest rival framing — a different control,
  population, or surface a careful reader might insist on — and settle it
  empirically: adopt it, or run the cut that discriminates between the frames and
  log the result; the rival and the verdict go in the same block. A rival may be
  dismissed without running it only when the data to run it genuinely doesn't
  exist — name the missing column or table. "The ideal design isn't available"
  never qualifies: when the clean design is out of reach, name the best
  discriminating cut the data in hand *does* support and run that instead. A
  rival named in the contract and then neither run nor shown unrunnable is the
  single most common wrong-answer signature — the caveat reads as diligence
  while the uncontrolled comparison drives the verdict. A steer or discovery that
  changes the estimand, population, comparison design, or decision surface gets a
  fresh contract entry; revise affected calculations and conclusions accordingly.
  A wrong first framing survives every downstream check; this is the only gate
  that catches it.
  What to choose is still your judgment — the rule is only that the choice is
  written down and challenged before it hardens.
- **Run the flip test before shipping a recommendation.** When the brief recommends
  an action (roll back, keep, change a policy), identify the one cut most likely to
  reverse that recommendation — for a comparison across versions or periods, that is
  usually the incumbent's own history over the same calendar window — and run it
  before writing the brief. Log the cut and its result, whichever way it lands. If
  it genuinely cannot be computed from data in hand, the recommendation is stated
  as conditional on that untested confound — in the executive summary, not a
  footnote. This gate applies to the recommendation only, not to every rival
  mentioned in passing; it is one cut, not a sensitivity sweep.
- **A surfaced source gets opened, not noted.** When the run surfaces a more
  authoritative source than the one in hand for a load-bearing claim — an owning
  team's table, a canonical dataset, a KB pointer, a retained artifact — open it,
  then one of three: use it; log why, once opened, it doesn't fit the question; or
  log the verbatim failure (with credentials omitted: error, permission denial, missing path) from actually
  attempting it. Never ship an answer from a proxy while a surfaced authoritative
  source sits merely noted: "the canonical source probably exists" and "the canonical
  source was checked" support different conclusions. Opening a source doesn't relax
  the evidence rule — numbers still come from data computed this run: a canonical
  table is queried, not quoted.
- **External figures: fetched, never recalled.** A number from model memory — a
  benchmark, a market size, an industry rate — never enters the run; that ban is
  the point, not a formality. A figure *fetched this run* (a KB file opened, a URL
  retrieved, a document read) may enter, but only as labeled external context: cited
  with source and retrieval date, saved to `scratch/` as its instrument (the excerpt
  or fetched file plays the role the SQL plays for a computed number), and kept
  visually separate in the brief — an assumption that frames the finding, never the
  finding itself. Headline claims are still carried only by numbers computed this
  run; if the conclusion would flip within the plausible range of an external
  figure, say so where the figure is used.
- **Every reported number has a saved instrument.** Each instrument — a
  `scratch/<meaningful-name>.sql` query or a `scratch/<meaningful-name>.py` analysis
  script — is saved before or as it runs; the log entry for the number points to it.
  A number nobody can reproduce is a provenance gap.
- **A failed query is not an empty result.** A missing table, unresolved column,
  permission error, or timeout is "not runnable — instrument gap", never "no rows found".
  The two support opposite conclusions. Log the error verbatim, omitting credentials.
- **Recompute the headline once.** Before writing the brief, check the headline number by
  an independent path — a different grouping that must sum to it, a rate rebuilt from its
  numerator and denominator, a second table that should agree. Log the check and its result.
- **Sum checks on decompositions.** Any split (mix vs. within, bridge legs) must
  reconcile to the total it explains; state the residual.
- **A material residual is a to-do, not a caveat.** Before shipping, either name it
  (finer cells, the correct attribution layer for the leg, added mix dimensions,
  entering/exiting made explicit) or show it sits inside the noise floor
  (leave-one-out / day sensitivity). Park it as an identification gap only when the
  data genuinely doesn't exist — not when the legs are merely too coarse. Two standing
  traps: (a) diagnostics computed mid-run that would shrink the residual but never get
  promoted back into the published decomposition — before closing, re-check `scratch/`
  for exactly this; (b) "need more mature days" — before waiting on the calendar, check
  whether re-aligning the endpoint (e.g. a fixed short horizon both periods satisfy
  today) unlocks the comparison now.
- **Fully qualified table names** in all SQL, always. For local files the equivalent
  is an absolute path in the reader (e.g. `read_csv_auto('/abs/path/drives.csv')`) —
  never a relative path that depends on the working directory.
- **Warehouse writes stay session-scoped.** Temp tables and other session-scoped
  objects are fine when a multi-stage query wants one — log the DDL like any
  instrument. Persistent warehouse objects (tables, views, materializations) are
  repo-edit-grade: only on explicit user request.
- **All analysis Python runs through `uv run`** (project env, default libraries
  preinstalled) — never system Python, never `--break-system-packages`. The mechanics
  are in `INSTALLATION.md`; read it at run start, not after something fails.
- **Local files are a first-class source.** When the data is CSV/Parquet on disk rather
  than a warehouse, DuckDB is the query engine and every rule above still applies:
  absolute paths play the role of qualification, every load-bearing query is a saved
  instrument, and aggregates-only still governs what enters the conversation. A
  public dataset downloaded this run and queried like any local file is run-computed
  evidence, not external context — log the source and retrieval date next to the
  pull, then treat it like any other table.
- **Row-level extracts are opt-in, per run.** The default stands: no record-level
  data in `scratch/`. When a method genuinely requires unit-level local compute —
  matching, unit-level modeling, survival analysis, record-level resampling — ask,
  and proceed only on the user's explicit OK for that run. Then: pull only the
  columns the method needs, drop or hash direct identifiers, and open the run-log
  entry with the aggregate-insufficiency case — why no finer aggregation answers the
  question (if one does, use it instead). The extract is consumed only by scripts
  whose printed output is aggregate: never `head`/`cat` it, never echo rows into the
  conversation, never quote it in a deliverable. Delete the extract at run close —
  the pull SQL stays in `scratch/` as the reproducible instrument, so nothing
  row-level survives the run at rest.
- **Keep raw responses out of the conversation.** Slice query output to the needed
  aggregates (e.g. with `jq`) and write anything bulky to `scratch/` — a bloated
  context makes every later step, and every prompt-cache miss, more expensive.
  For long-running queries, use the warehouse's asynchronous API, record the query ID
  alongside the saved SQL, work on independent tasks, and poll according to the
  provider's documented limits.
- **DuckDB for local work (optional).** When an analysis needs joins, reshaping, or
  iteration that would be slow as repeated warehouse round-trips, pull the needed
  *aggregates* once into `scratch/` (CSV/Parquet) and work them locally with `duckdb`.
  Keep the pull SQL and the local SQL both in `scratch/`. Don't reach for this on simple
  pulls — the warehouse is fine.

## Reference material

Any live internal knowledge bases you maintain — e.g. a sibling repo checkout, a wiki
export, or domain playbooks. Read them for table choice, required filters, encoding
gotchas, business interpretation, and narrative style — **KB prose is routing and
interpretation, never evidence**; claims come only from data computed this run. (A
figure quoted in KB prose may appear in a brief only via the external-figures
channel in Rigor — labeled context, never a finding.)

Configure your own roots here as you adopt them, e.g.:

| Domain | Root | Start at |
|---|---|---|
| *(example)* Some domain KB | `../<your-kb-repo>/<domain>/kb/` | `orientation.md`, then `rules/<topic>.md`; escalate to `reference/<topic>.md` for mechanism/schema |

*No KB roots are configured yet — the row above is a template. Until one is added,
note the gap in the log and work from first principles.*

For a table whose filters or units aren't obvious, check the KB **before** computing —
shared tables often need a type filter, rate columns may be decimal fractions, a
category field may be a string bucket, and cohort-date choice matters. The KB holds
the current list; don't trust memory over it. If a KB root is missing, note the gap
in the log and continue from first principles.

## Done when

The run folder holds all four deliverables with `brief.html` as the current answer (no
stale variants at the root), every load-bearing number in the brief traces through
`run_log.md` to a `scratch/` instrument, the coverage check is logged, and the user got
the answer in chat with a pointer to the brief.
