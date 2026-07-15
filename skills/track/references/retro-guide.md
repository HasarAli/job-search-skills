# Retro guide

Run when application count crosses a multiple of `retro-every` (default 50, set in `search/search-config.md`), or on demand ("how is my search going").

## Delegate the analysis

Spawn one subagent for the number-crunching so the main context stays small. Its task:

- Read `applications/applications.csv` and the JD snapshots in `applications/<id>.md`.
- Return only: the metrics below, the JD pattern summary, and any anomalies. No raw rows, no file dumps.

## Metrics to compute

Over the whole history and over the most recent batch (last `retro-every` applications) — the recent batch shows whether things are improving:

| Metric | Formula |
|---|---|
| Response rate | applications reaching `screen` or beyond ÷ total (exclude applications younger than `follow-up-days` — too fresh to count as non-responses) |
| Screen rate | same numerator ÷ total resolved (terminal + past-threshold) |
| Screen → interview | reached `interview-1`+ ÷ reached `screen` |
| Interview → offer | reached `offer` ÷ reached `interview-1` |
| Rejection/ghost split | terminal rows by `rejected` vs `ghosted` |

Present as a funnel: applied → screen → interview → offer, with counts and conversion percentages between stages.

## Mining applied JDs for patterns

From the JD snapshots in `applications/<id>.md`, extract:

- **Titles** — most common titles applied to; do they match the role list in `context/role-preferences.md`?
- **Keywords** — recurring required skills/tools across JDs; are the top ones present in the current resume and `context/highlights.md`?
- **Seniority** — level distribution (junior/mid/senior/staff equivalents in this industry); is the user applying above, at, or below their positioning?

Then split every metric by segment (title, seniority, source board): a 0% response rate on one role and 8% on another is a targeting answer, not a resume answer.

## Adjustments by failure point

| Symptom | Likely leak | Consider |
|---|---|---|
| Few/no responses (below ~1/50) | Resume or targeting never passes the first skim | Resume rewrite against the mined JD keywords (`resume` skill); revisit role targets or seniority (`onboard` targets); loosen or refocus filters if volume is also low |
| Screens but no interviews | Positioning or screen performance | Sharpen the positioning story for screens; review recurring screen questions in `<id>.md` notes; add screen-prep tasks to `state.md` |
| Interviews but no offers | Interview performance | Identify which round/type fails from event notes; targeted prep tasks in `state.md`; consider mock interviews with the advisor agents |
| High ghost rate on one source | Board or channel quality | Deprioritize that source in `search/job-search-filters.md` |

The ~1/50 response-rate trigger is a prompt to review, never an automatic change — benchmarks differ per industry, country, and market cycle. Present the numbers and the options; the user decides.

## Sample sizes — do not overreact

- Under ~20 resolved applications, conversion rates are noise. Report them, but recommend no changes except fixing obvious errors (wrong resume attached, broken links).
- Change one variable at a time (resume, targets, or filters), then measure the next batch against the previous one. Simultaneous changes make the next retro uninterpretable.
- Late-stage rates need late-stage volume: with 2 interviews, interview→offer of 0% means nothing. Say so explicitly rather than prescribing prep.
- Ghosting is background noise in every market; a high ghost rate alone is not a signal unless concentrated in one segment.

## Closing the retro

1. Record learnings and agreed prep tasks in `state.md`.
2. Route agreed adjustments to the owning skill; do not edit resume/targets/filters from within `track`.
3. Remind the user to commit — the retro is part of the audit trail.
