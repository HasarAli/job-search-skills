---
name: goals
disable-model-invocation: true
description: >-
  Use only when the user explicitly asks to set, review, or rework what they are
  searching for — role targets, seniority, and positioning into
  `goals/role-preferences.md`; comp, location, company, logistics, and the
  search cadences into `goals/search-filters.md`.
---

# Goals — decide what to search for

You are the user's **advisor**. Where they are decided, record it in their words and move on. Where they hesitate, put the trade-off in front of them and recommend one side of it, grounded in what `career/profile.md` already says — an unanswered question is a hole in the search, and silence is not a value.

**Prerequisites** — read `career/profile.md`; recommendations come out of it, so an empty one hands off to `intake`. Read the existing `goals/*` files: a rework changes what the user names and leaves the rest standing.

Ask one question at a time and wait. Trade-offs, defaults, and what in the profile grounds each recommendation: [references/decision-guide.md](references/decision-guide.md). Market norms: `.agents/config/conventions/country-conventions.md` and `.agents/config/conventions/industry-conventions.md` — use the country and industry rows to frame the choices, not just to fill a field.

## 1. Identity and market → `goals/search-filters.md`

Country or countries searched, industry, working language and application language, employment status and any confidentiality need. Record the dominant platform the country row names — `resume` and `optimize-linkedin` read their conventions out of this file. Which boards and channels to actually search belongs to `sources`.

Done when: the "Identity & logistics" section carries a value for each, dominant platform included.

## 2. Role targets → `goals/role-preferences.md`

Target titles ranked under "Targets — apply now", each with one positioning anchor — the single line that says why this user fits that title. Then the seniority band and whether one level down is acceptable, any stretch role to keep on the radar, and under "Do not pursue" the titles, patterns, and work styles to skip even when they match on paper.

A target with no anchor is a title, not a target: build the anchor with the user out of `career/profile.md` before moving on.

Done when: every target carries a positioning anchor, the seniority band records the one-level-down answer, and "Do not pursue" exists.

## 3. Comp → `goals/search-filters.md`

Walk-away floor and target in total comp, the currency and cadence the market quotes in, and non-salary must-haves — equity, pension, healthcare, bonus. Where the floor and the target market's bands disagree, say so and let the user set the number.

Done when: floor, target, currency, cadence, and must-haves each have a value.

## 4. Location and company → `goals/search-filters.md`

Remote, hybrid, or on-site — what is acceptable and what is preferred; commute range; relocation appetite and its terms; company type, stage, and size; hard culture filters such as on-call or shift work.

Done when: each has a value, and every hard filter is written as a filter a search run can apply.

## 5. Logistics, authorization, cadences → `goals/search-filters.md`

Earliest start date and notice period, travel tolerance, hours constraints, and work authorization in each target country — already authorized, or sponsorship needed. Then the cadences other skills read: `follow-up-days` (default 14) and `retro-every` (default 50).

Done when: each has a value and both cadences are written as named settings — "no constraint" counts as a value, an unasked question does not.

## 6. Report and record

Report the targets and the filters back as the search they define, and name the two or three decisions the user was least sure about — those are what a `retro` revisits first. Check off the `goals` stage in `.agents/state.md` and commit `goals/`.

Done when: both files are written and committed, and the `goals` stage is checked off.
