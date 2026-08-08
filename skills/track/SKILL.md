---
name: track
description: >-
  Log one application event onto its row in `applications.csv`, then sweep for
  stale applications that need a nudge. Use when the user reports a recruiter
  reply, rejection, interview, or offer, when
  `inbox` hands over an application-status signal it read on a channel, or when
  the user wants follow-ups checked. Reading inbound recruiter threads belongs
  to `inbox`; submitting an application and creating its row belongs to `apply`;
  the response-rate analysis belongs to `retro`.
---

# Track — outcomes and follow-ups

You log what is reported and propose everything else: the user sends every follow-up and confirms every ghost. A subagent may read `applications.csv`; facts from `career/` and `goals/` docs travel inline in the prompt you write.

**Prerequisite** — read `applications.csv`. A missing CSV means nothing is tracked yet: hand off to `apply`.

## Files and settings

- `applications.csv` — one row per application, and the whole record. Column contract: apply's [references/record-format.md](../apply/references/record-format.md).
- `goals/search-filters.md` — `follow-up-days` (default 14), `retro-every` (default 50).

Stages: `applied → screen → interview-N → offer | rejected | ghosted`. Definitions, transitions, the event→stage map, and the ghost bar: [references/stages.md](references/stages.md).

## 1. Log the event

The event comes from the user directly, or from `inbox` handing over a recruiter reply, rejection, or interview invitation it read on a channel.

1. Match the event to a row by company and role; ask when two rows could fit.
2. Set `status` from the event→stage map and `last_activity` to today.
3. Rewrite `notes` so it reads as where this application stands now, the event's own words kept where they carry detail: who reached out, the format, what was scheduled, what the user learned. A retro two months out reads this, and paraphrase loses the round that failed. What the event superseded comes out.
4. Set `next_action` and `next_action_date` to the move the event created — the user's reply to draft, the invitation to answer, the follow-up date when the ball is the company's. A terminal `status` empties both.

A learning the event carried lives in `notes` and is named in the closing report — it goes nowhere else.

Done when: the row's `status`, `last_activity`, `notes`, and `next_action` pair all describe the application as it stands after this event.

## 2. Sweep for stale rows

Every invocation, once the user's request is handled.

A row is stale when its stage is non-terminal and either its `next_action_date` has passed or `last_activity` is older than `follow-up-days`. List each: company, role, stage, the overdue `next_action`, days silent. Offer three moves per row — draft a nudge for the user to send, propose `ghosted` against the ghost bar in [references/stages.md](references/stages.md), or push the date out — then log whichever the user picks as an event (step 1).

Done when: every stale row carries the user's choice, and each nudge, ghost, and pushed date is on the row.

## 3. Close

Report the row you moved, the stale rows and their choices, and any learning the event carried.

When the total application count crosses a multiple of `retro-every`, say so and offer `retro` — the analysis runs there, not here.

Tracker writes are the audit trail: offer to commit `applications.csv`.

Done when: the report is with the user, the retro offer is made if the count crossed, and the commit offer is with the user.
