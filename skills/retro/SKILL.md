---
name: retro
disable-model-invocation: true
description: >-
  Response-rate retro over the applications so far: compute the funnel, split it
  by segment, name where it leaks, and route each agreed adjustment to the skill
  that owns it. Use only when the user explicitly asks how the search is going,
  asks why nobody is replying, or accepts the retro `track` offered on crossing
  a multiple of `retro-every`. Logging a single outcome and sweeping stale rows
  belong to `track`.
---

# Retro — find the leak

You compute and present; the user picks what changes. Every agreed adjustment is executed by the skill that owns it, in this session or the next.

**Prerequisites** — `applications.csv`, and `goals/search-filters.md` for `retro-every` (default 50) and `follow-up-days` (default 14). A missing CSV means nothing to analyze: hand off to `apply`.

## 1. Scope the period

The user names it: a date range, the last N applications, or the whole history. With nothing named, run the whole history plus the last `retro-every` applications side by side.

Done when: the period is stated back to the user as a date range and an application count.

## 2. Compute and present

Run it from [references/retro-guide.md](references/retro-guide.md) — delegation, metrics, segment split, the leak table, loop diagnosis, and the noise floor.

Present the funnel — applied → screen → interview → offer — with counts and conversions between stages, then the same metrics split by title, seniority, and source board. Name the leak, or say the numbers sit under the noise floor and name that instead. Under the floor, the honest answer is that there is nothing to conclude yet.

Done when: the funnel with counts and conversions is presented, split by segment, and the leak is named or explicitly called noise.

## 3. Route the adjustments

The user picks the changes. Each one goes to its owning skill, carrying the finding that motivated it:

| Adjustment | Owner |
|---|---|
| Bullet wording, missing keywords, weak metrics | `highlights` |
| Which bullets ship, resume assembly, re-render | `create-resume` |
| Role targets, seniority, comp, filters | `goals` |
| Boards, ATS targets, coverage | `search` |
| Channel coverage, reply handling | `inbox` |
| Headline, About, profile copy | `optimize-linkedin` |
| Recurring screen questions, a failing round | `interview` |
| Standing technical practice | `teach` |

Agreed actions are reported to the user and handed to the owning skill. No file collects them.

Done when: every agreed adjustment names its owning skill and has been handed over or reported to the user, and the one variable changing this round is stated.
