---
name: highlights
description: >-
  Mine the user's history for resume-ready achievements and settle their
  quality: probe role by role newest-first, write each achievement as an XYZ
  bullet, get a number or a visible placeholder onto it, score it on the
  skim/level/tier rubric, and write `career/highlights.md`. Use when the user says
  "work on my highlights", "I shipped something worth adding", or "my bullets
  are weak", and when `career/highlights.md` is missing or thin for a role.
  Choosing which bullets go on a resume and rendering the PDF belong to
  `create-resume`; recording raw career facts belongs to `intake`.
---

You mine and score; the user supplies the numbers and picks which rewrites ship — apply exactly what they select. Take every number as given.

**Prerequisites** — read `.agents/state.md`, `career/profile.md`, `career/career-diary.md`, and `career/highlights.md` if it exists. A missing `career/profile.md` or `career/career-diary.md` hands off to `intake`.

Steps 2–6 run once per role, most recent first. Everything already in `career/highlights.md` keeps its section number and its id — a run adds sections and entries, it never renumbers.

## 1. Pick the roles to mine

List the roles in `career/profile.md` newest first, with the bullet count `career/highlights.md` already carries for each. The target is 2–4 bullets per role, more for recent roles and roles close to the targets in `goals/role-preferences.md`. Ask the user which roles this run covers; a run for one new achievement covers one role.

Done when: the user has named the roles for this run, in reverse-chronological order.

## 2. Probe the role

Ask about one role at a time, one question per message, and probe once for depth. Mine the role's lines in `career/career-diary.md` and `career/profile.md` first and confirm what they already answer — "the diary says you cut report turnaround to a day at Acme; what did that unlock?" — rather than asking it cold. Hunt for shipped outcomes: what got faster, cheaper, larger, more reliable; what the user decided; who they unblocked or mentored.

Done when: the role has at least 2–4 candidate achievements, each with an outcome and a method.

## 3. Draft the bullets

Write each achievement as an XYZ bullet — accomplished X, as measured by Y, by doing Z — against the standard in [references/bullet-rubric.md](references/bullet-rubric.md). Split compound achievements into one idea per bullet.

Done when: every candidate achievement is a single XYZ bullet, outcome first.

## 4. Fill the metrics

For each bullet, propose a few candidate metrics — concrete things that could measure it (% latency cut, engineers unblocked, revenue attributed, time saved per week, users served) — and ask which of them the user can put a number to. One bullet per message. Write the number the user gives straight into the bullet. A metric they don't have becomes a `{{METRIC: what would measure it}}` placeholder that travels through to the resume, visible — a visible placeholder is recoverable, a fabricated number is not.

Done when: every bullet holds a number or a placeholder.

## 5. Score and rewrite

Score every bullet on all three lenses — skim, level, tier — and write the rewrite each low score calls for: [references/bullet-rubric.md](references/bullet-rubric.md).

Done when: every bullet carries three scores plus either one rewrite or "ships as-is".

## 6. The user picks the rewrites

Show original vs. rewrite per bullet, with the scores that motivated it. Keeping the original is always on the table. Apply exactly the user's selection. A rewrite that needs an unrecorded fact earns one question.

Done when: every scored bullet has a recorded verdict — rewrite or original.

## 7. Write the role's section

Append the role's bullets to `career/highlights.md`, grouped under the role held when the work shipped, sections numbered continuously from the file's current highest section so every bullet is addressable as `section.entry` (`2.4`). A new bullet for a role that already has a section takes the next entry number inside it. Append every fact learned during probing to `career/career-diary.md` verbatim, and add any new skill, story, or gap to `career/profile.md`.

Done when: the role's bullets carry ids in `career/highlights.md`, and each new fact appears in `career/career-diary.md`.

## 8. Report and record

Return to step 2 for the next role back until this run's roles are done. Then report the ids written per role and every `{{METRIC: …}}` still open, and update the `highlights` stage in `.agents/state.md`.

Done when: every role in this run is written, open placeholders are reported, and the `highlights` stage is updated.
