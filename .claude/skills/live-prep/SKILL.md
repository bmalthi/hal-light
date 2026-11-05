---
name: live-prep
description: >
  Produce workspaces/<run>/live_prep.md — the presenter's defense doc for a live
  discussion of an analyse-run brief. Anticipates probing questions (why this method,
  what you didn't do, where you could be wrong, what would change your answer) and
  pre-loads honest, specific answers calibrated to what the presenter can actually
  defend. For the presenter, not the audience. Use when the user will present, walk
  through, or defend an analysis live — never shipped to the audience.
---

# live-prep — the presenter's defense doc

Produces `workspaces/<run>/live_prep.md` — the doc the presenter wants open on a
second monitor walking into the live discussion.

**This is not the brief and not the deck.** Those are for the audience. This doc is
for the presenter — honest, specific, sometimes self-critical, never shipped to the
room. It lives at the run root as a named extra deliverable: log it in `run_log.md`
and `methodology.md` per the `analyse` skill's clean-root rule.

## Why this exists

A shipped analysis is usually followed by a live discussion. The room probes:

- *Why this method and not that one?*
- *What did you choose not to do, and why?*
- *Where could you be wrong?*
- *What would change your answer?*
- *If you had another week, what would you do first?*

If these aren't pre-loaded, the presenter improvises — and improvises badly under
pressure, when the answer that came easily during analysis feels suddenly slippery
in a room of skeptics.

## Sources

Everything in this doc projects from the run's own record — never from memory:

- **`brief.html`** — the findings, headline numbers, and watch-items. Section
  anchors ("brief §N") point here.
- **`run_log.md`** — the framing contract (estimand, population, comparison design,
  rival framings and their verdicts), the flip-test result, decisions, ruled-out
  branches, and user steers.
- **`methodology.md`** — tables, filters, and how each headline was computed.

If this doc needs a claim the run record doesn't carry, that's a gap in the run
record — fix it there first.

## Sections

The doc has 7 sections in this order, after a §0 header. **§1 and §2 are the
highest-leverage prep** — a live room spends disproportionate time on confidence
calibration and forward-looking moves (the questions that can't be pre-baked into
the brief). Lead with these; everything below is ammunition.

### §0 — Reader header
One paragraph naming: (a) this doc is for the presenter only — never shipped to the
audience; (b) it is structured around anticipated questions, not around the findings;
(c) Tier-3 honest deferrals are explicit and acceptable — *inventing an answer is
worse than honest deferral with a named follow-up*.

### §1 — The one-sentence answer
**Top of doc.** The single sentence the presenter gives if the room asks *"so what
did you find?"* Memorize it. If the finding can't be compressed to one sentence, it
isn't yet understood well enough to defend.

### §2 — Confidence + next moves (the differentiator)

Two parts:

**§2a. How confident, and what would change that?**
- A single calibrated statement: *"Confidence in the headline: ~70%. The 30% comes
  from [specific open risk] — if [specific check] came back clean, I'd move to 85%."*
- **Avoid "fairly confident" / "pretty sure" / "reasonably certain"** — these read
  as evasive. Pick a number, defend it.
- The risks cited here must be the same ones in §5 and the brief's watch-items —
  consistency matters.
- **Numeric probabilities require a Tier-1 or Tier-2 defensible chain of reasoning.**
  If defending the number is Tier-3 territory for this presenter, drop it and use
  categorical confidence (High / Medium / Low) with a one-sentence reason — see
  Presenter calibration below.

**§2b. The 2–3 highest-leverage next moves, each with answer-shift tails**
- Not a wish-list of every possible follow-up. Two or three, ranked.
- Each move: (i) what you'd do, (ii) what data/access/time it requires, (iii) **how
  the current answer moves under each outcome** of that move.
- The "how it'd change the answer" tail is the whole point. *"I'd run more tests"*
  is a non-answer. *"I'd run X, which would move my confidence from 70% to 90% if it
  came back clean, or shift the recommendation from launch to hold if it came back
  skewed"* is the answer the room wants.
- If the answer-shift tail can't be written, the move isn't well-defined enough yet.

### §3 — What you did, and why this method
**Anchor on the brief.** Per finding (= per brief section), 2–3 bullets PLUS a tier
label:
- **Brief §N — <section headline>:** name the section the presenter will point to
  live.
- **Method used:** the actual technique.
- **Why this, not the alternative:** name the alternative explicitly. *"Used
  difference-in-differences instead of simple before/after because the control
  segments let us strip out the baseline trend."* The framing contract's rival
  framings and their verdicts are the first place to look.
- **Result:** the headline number with units and range — the same number the brief
  carries.
- **Tier label** (required): one of `(Tier 1 — defend cold)`, `(Tier 2 — intuition
  only, deeper math deferred)`, or `(Tier 3 — honest defer)`. See Presenter
  calibration. For Tier 3 entries, the bullets above are replaced by a scripted
  honest-deferral line — never write a methodology defense the presenter cannot
  deliver on the day.

When asked *"how did you find this?"*, the answer is *"brief §N — let me walk you
through it"*, with the matching deck slide (if one exists) as the visual aid.

### §4 — Hard choices, with "if wrong"
The decisions that could have gone either way. Format per choice:

- **Decision:** what was done. **Brief §:** the section it shapes (or "structural —
  applies across §N…§M").
- **Alternative:** what wasn't done.
- **Why this:** the reason — time budget, data shape, signal-to-noise.
- **If wrong:** what changes in the final answer (and which brief section would need
  rewriting).

Source: the decision bullets in `run_log.md` — including ruled-out branches and
mid-run reversals. Reversed decisions are especially interesting live: they
demonstrate ownership, not weakness.

The "if wrong" line is non-negotiable. *"You used the median — why not the mean?"*
If that can't be answered in two sentences from this section, the presenter isn't
ready.

### §5 — What's missing (gap + assumption table)
For each load-bearing assumption:

- The gap (what data we wished we had).
- The assumption made in its place.
- **Sensitivity:** quantified if possible. *"If the assumption is off by 20%, the
  effect moves from +5% to +3% — sign holds. If off by 50%, sign could flip."*
- **Brief §N affected:** which section's takeaway moves under the sensitivity.

The brief's watch-items carry the same content — if the two diverge, fix the brief
first; this section projects from it. Sensitivity matters more than the assumption
itself. *"Could be wrong"* is not a defense. *"Could be wrong in a way that moves
the answer by X"* is.

### §6 — What you didn't do, and why
Hypotheses dropped, methods skipped, segments not cut. Each with a reason.

> *"Didn't run X because Y"* is a much better answer than *"didn't think of X"* —
> and it will be asked.

Typical entries:
- Hypotheses raised early that didn't survive validation (with reason).
- Cuts considered but skipped (e.g. *"didn't cut by segment S — missing for 40% of
  rows, would have been more noise than signal"*).
- Methods known but not applied (e.g. *"didn't bootstrap CIs — sample was large
  enough that analytic intervals were tight"*).
- Explicit honest-deferral entries: *"I can defend [X intuition]; the deeper [Y] I'd
  defer on; the follow-up that resolves it is [Z]."*

(Forward-looking "what's next" content lives in §2b. The room goes there first.)

### §7 — Q&A anticipation
Top 5–10 likely questions, with 2–3-sentence answers. Drawn from:

- Every watch-item in the brief → predict the skeptical re-ask.
- Every §4 hard choice → the alternative path is the natural challenge.
- The biggest claim in the executive summary → what's the obvious skeptical question?
- Anything the ask named that couldn't be fully answered → expect it directly.

For each:

```
Q: <skeptical question, verbatim>
A: <2-3 sentence answer using: claim, evidence, bias-direction>
```

The bias-direction argument is the move that wins the room. *"Even if the assumption
breaks, the direction of bias is conservative — we'd be under-estimating, not
over-estimating. The point estimate is a floor."*

## Presenter calibration

A live_prep doc is only useful if the presenter can actually deliver what's in it.
Calibrate the doc to the presenter's *actual defensive surface*, not to an idealized
analyst's. Every line must be deliverable under pressure without notes — a
confident-sounding methodology defense the presenter can't reproduce on the day is
worse than honest deferral with a named follow-up.

Classify every methodology choice in §3, every confidence number in §2, every Q&A in
§7, and every entry in §6 into one of three tiers:

**Tier 1 — defend cold.** The presenter understands the choice fully and can deliver
a 1–2 sentence defense without notes. Pure economic logic, arithmetic, standard A/B
mechanics, audience-readable inference. Write these as confident defense lines.

**Tier 2 — intuition only.** The presenter understands the WHY but not the deeper
math — e.g. maturity-equalized comparisons ("time-balanced the arms"), hazard-style
recipes ("unmatured cohort = early-window observation"), shrinkage-style estimators
("pull noisy cells toward the overall mean"). Defend the intuition confidently;
route the deeper HOW to "methods-review territory" in a single closing sentence.

**Tier 3 — honest defer.** The presenter cannot defend the deeper math at all —
named statistical machinery (Cox PH vs IPCW, bootstrap-CI mechanics, hierarchical
Bayesian shrinkage, prior-sensitivity math). Write a *scripted honest deferral* —
never a defense the presenter can't deliver.

**Standard deferral patterns** (use verbatim when they fit):

> **Methodology-depth defer:** "Honest answer — I'd defer to a methods review on
> [specific X]. What I can defend is [intuition Y]. The direction is robust; the
> [precise number / specific choice] is where I'd want deeper sign-off before it
> locks a high-stakes decision."

> **Unfamiliar-stat-name defer:** "I'm not the right person to defend [named method]
> versus the alternative on this dataset — that's a methods-specialist call. The
> intuition I worked through is [Y]. The sensitivity sweep showed [Z]. The direction
> held."

> **AI-tool-use frame** (when the presenter wants to surface the analytical stack
> honestly): "I used the analytical toolkit to surface this option set; the intuition
> I validated against is [Y]; the deeper math is methods-review territory."

The mix of tiers reflects the presenter's actual depth — a stats-strong presenter
will have more Tier 1; a stats-lighter presenter more Tier 3. **Both are valid and
both produce defensible docs.** What's not valid: a Tier-1 defense written for a
choice that's actually Tier 3 for this presenter. That's the failure mode this skill
exists to prevent. If the presenter's depth is unknown, ask before drafting — the
tiering can't be guessed.

**How to determine tier per choice:** ask *"if a senior skeptic pushed on this for
2 minutes, what could the presenter say without notes?"* Coherent defense → Tier 1.
Intuition without the math → Tier 2. "I'd want a colleague who knows X" → Tier 3.

**Where calibration applies:**
- §2a — categorical confidence + reason is always safe; numeric probabilities
  require a Tier-1/2 defensible chain
- §2b — answer-shift tails as plain-English parameter sensitivities (Tier 1/2), not
  posterior-probability phrasing (Tier 3)
- §3 — every entry carries an explicit tier label; Tier 3 entries are scripted
  deferrals, not defenses
- §4 — "if wrong" lines in mechanism language, not statistical phrasing
- §5 — sensitivity brackets reported verbatim from the run's computed checks
- §6 — explicit honest-deferral entries with named follow-ups
- §7 — Q&A responses must match the tier of the underlying §3 entry

## Workflow

1. Draft after the brief ships — after the `analyse` run's coverage check and static
   check have passed — so every §3/§4/§5 entry projects from a settled `brief.html`,
   `run_log.md`, and `methodology.md` rather than a moving target.
2. Draft → re-read → trim. A deliberate gap before the re-read sharpens what to cut.
3. Output: `workspaces/<run>/live_prep.md`, logged as an extra deliverable in
   `run_log.md` and `methodology.md`.
4. If there's no live discussion scheduled, producing it can still be worth it on an
   analysis someone will challenge — it forces the same rigor and often surfaces
   inconsistencies in the brief. Only on explicit request, though: it is not a
   default `analyse` deliverable.

## Output contract

`workspaces/<run>/live_prep.md` exists, with §0 header + §1–§7 filled, and:
- §0 names: presenter-only audience, question-anchored structure, Tier-3 deferrals
  explicit and acceptable.
- §2a has a **calibrated** confidence — numeric (with a defensible chain) OR
  categorical (High / Med / Low + one-sentence reason). Not "fairly confident."
- §2b has 2–3 ranked next moves, each with an **answer-shift tail** in mechanism
  language.
- §3 entries each carry an explicit **tier label**; Tier 3 entries use scripted
  deferral lines.
- §4 entries each have an "if wrong" line in mechanism language.
- §5 entries each have a quantified or qualitative sensitivity note.
- §6 includes any honest-deferral entries that map to anticipated questions.

If any of those is missing, the doc isn't done.

## Tone

- **Honest.** The doc is for the presenter. If a finding is weak, write that.
  Unsupported certainty makes the discussion harder to defend.
- **Specific.** *"We could be wrong"* is useless. *"We could be wrong by ~N units
  if X"* is useful.
- **Terse.** Bullets, not paragraphs. It's skimmed under pressure.
- **Calibrated to the presenter's defensive surface.** Honest deferral with a named
  follow-up beats a confident defense the presenter can't execute.

## Anti-patterns

- **Writing this as a second brief or deck.** Not for the audience; don't polish.
- **Defensive padding.** "The methodology was rigorous" sentences are wasted.
- **Listing every limitation.** Three thought hard about beat ten listed
  mechanically.
- **Hiding what wasn't done.** The room asks about §6 disproportionately often.
- **Vague confidence.** *"Pretty confident"* reads as evasive. Pick a number — or
  categorical High/Med/Low with a one-sentence reason.
- **§2b with 10 next moves.** More than three signals no prioritization.
- **§2b moves without answer-shift tails.** Without the tail, the move is a wish.
- **Methodology defenses the presenter can't deliver.** If §3 reads like a stats
  grad student and the presenter can't reproduce it under pressure, the calibration
  failed — route to Tier 3 with a scripted deferral.
- **Tier-3 entries without a named follow-up.** Honest deferral isn't "I don't
  know" — it's "I can defend X, would defer on Y, the follow-up that resolves Y is
  Z." Without the follow-up, the deferral reads as a dodge.
- **Statistical phrasing in §4 if-wrong lines.** *"Under prior P3 the posterior
  flips"* won't be deliverable. *"If marginal converters cancel at 2x the pooled
  rate, the ROI flips and we'd notice via [signal]"* will be. Mechanism language
  beats statistical language for live delivery.
