# Bullet rubric — the standard, the three lenses, the rewrite

Every bullet in `career/highlights.md`, every resume highlight, and every rewrite is written and scored against this file.

- [The standard](#the-standard) — what a shippable bullet looks like
- [The three lenses](#the-three-lenses) — skim, level, tier, with score anchors
- [Scoring and rewriting](#scoring-and-rewriting) — how the pass is reported

## The standard

> **Accomplished [X] as measured by [Y] by doing [Z].**

- **X** — the outcome: the product or business result.
- **Y** — the measure: a number, percentage, time saved, revenue, scale, adoption.
- **Z** — the method: what the user did, with the concrete tools or approach.

- ✗ "Responsible for the reporting pipeline."
- ✗ "Rebuilt the reporting pipeline using new tooling." (activity, no outcome)
- ✓ "Cut monthly report turnaround from 5 days to 1 by rebuilding the reporting pipeline around automated data pulls."

Order flexes for readability — Z-first works when the outcome still lands early — and all three parts stay present. A bullet with no Y earns a metric question, not a slot on the page.

Voice:

- Open on a past-tense action verb; present tense for ongoing work in the current role, consistent within an entry.
- Active voice, no pronouns: "Reduced costs by…".
- Name the action that was taken — "Owned the migration" where "Responsible for", "Helped with", "Worked on", "Assisted in" say nothing.
- One idea per bullet; split compound achievements.
- 1–2 rendered lines. Three-line bullets get skipped.
- Vary the opening verb across a role's bullets.
- Plain human prose. Strip the AI tells: promotional adjectives ("cutting-edge", "seamless"), rule-of-three lists, em-dash pileups, trailing "-ing" clauses, "not X but Y", filler.

## The three lenses

Score every bullet 1–5 on each lens. Each lens anchors 1, 3, and 5; a bullet sitting between two anchors takes the 2 or 4 between them. The target level and tier come from the target's positioning in `goals/role-preferences.md`, plus company type and stage in `goals/search-filters.md`.

### Skim — the recruiter's ten seconds

The first pass is seconds per resume, and it screens out rather than in.

- **5** — the first 3–5 words name the outcome, a target-role keyword appears verbatim, and it renders in 1–2 lines.
- **3** — the outcome arrives late in the bullet, or the keyword shows up only as a synonym of the term the target uses.
- **1** — opens on the activity, the stack, or a duty phrase; or runs three lines.

Truncation check: cut the bullet mid-line — a 5 still tells the reader why it matters.

### Level — the hiring manager's calibration

Scope ladder, rung by rung: shipped a task → owned a feature → owned a system → owned a problem space → changed how other teams work. Senior owns a system or area end-to-end and mentors; staff sets direction across teams. Years held are a prior; scope shown is the evidence.

- **5** — scope at or above the target level's rung, carrying a scale number (users, requests, data volume, revenue, engineers mentored) and evidence the problem was found rather than handed down.
- **3** — the right rung with no scale number, or a scale number a rung below the target.
- **1** — a task-level claim, credit shared with no personal decision ("part of the team that…"), or leadership asserted with no headcount or outcome attached.

Probe test: write the interview follow-up the bullet invites ("what did you decide, and what would have happened without you?"). A bullet whose answer isn't already inside it caps at 3.

### Tier — how it reads at the target tier

Tiers differ: what impresses a traditional employer reads thin at a well-funded scaleup, and a scaleup number can be an order of magnitude short of a Big Tech bar.

- **5** — the number impresses at the target tier, and the bullet carries a standout signal: production scale, ownership beyond the assigned ticket, open source, technical writing, a project with real users.
- **3** — strong one tier down, thin at the target — the same work an order of magnitude smaller.
- **1** — positioned for a track the target rules out under "Do not pursue" (management mechanics against an IC target), or generic enough to sit on any resume.

Tailoring is reordering and reweighting for the target: the keyword list decides which bullets lead, never how often a term repeats.

## Scoring and rewriting

- Report each bullet as `id — skim/level/tier`, plus one line naming its weakest lens.
- Any lens at 3 or below earns exactly one rewrite, aimed at that lens and leaving the rest of the bullet alone. One rewrite, not a menu.
- All three lenses at 4 or above: "ships as-is".
- Facts and numbers survive a rewrite unchanged.
- A `{{METRIC: …}}` placeholder is a pending value: score the bullet as though the number were there, and carry the placeholder into the rewrite.
- A rewrite that needs a fact nobody recorded becomes a question for the user.
