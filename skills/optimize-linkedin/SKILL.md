---
name: optimize-linkedin
disable-model-invocation: true
description: >-
  Audit and optimize the user's live profile on a professional platform
  (LinkedIn by default): crawl it into a dated snapshot, score every section for
  findability, conversion, and consistency, then apply each approved rewrite in
  the browser one confirmed edit at a time. Use only when the user explicitly
  asks — "audit my LinkedIn", "optimize my profile", "rewrite my headline", "fix
  my About section", "should I turn on Open to Work", or why recruiters aren't
  finding them. This is an optional branch of the search, never a prerequisite
  for one. Resume bullets and PDFs belong to `create-resume`; writing the bullets
  themselves to `highlights`; answering recruiter messages to `inbox`.
---

The user picks which recommendations ship, and every edit gets its own yes before the browser touches the live profile.

**Prerequisites** — the `goals` and `create-resume` stages in `.agents/state.md` are both checked: a profile is positioned against decided role targets and a shipped resume, so an audit before either exists has nothing to score against. A missing stage hands off to the skill that owns it. The platform comes from `goals/search-filters.md`, LinkedIn by default. Browser tools work on the user's existing logged-in session; a logged-out session is a question for the user.

Re-runnable by design: each run crawls fresh, so a second round after the user has applied their own manual items scores the profile as it now stands.

## 1. Crawl (subagent)

Spawn one subagent to crawl the profile with browser tools and write the snapshot to `<platform>/<YYYY-MM-DD>-snapshot.md` (e.g. `linkedin/2026-07-09-snapshot.md`). Sections to capture, report format, and crawl conduct: [references/crawl-guide.md](references/crawl-guide.md). Relay the platform and profile URL inline in its prompt; `career/` docs stay in the main session. It returns the report path plus a 3–5 line summary, so the raw crawl stays out of the main session.

Done when: the report exists at the dated path and every row of the crawl guide's section table appears in it, verbatim text or marked missing.

## 2. Score every section

Score each section of the snapshot on all three lenses — findability, conversion, consistency — and write the rewrite each low score calls for: [references/review-rubric.md](references/review-rubric.md). Which fields carry the weight on this platform: [references/platform-notes.md](references/platform-notes.md).

Done when: every section in the snapshot carries three scores plus either one rewrite or "ships as-is", and the keyword-gap list names the recruiter queries the profile misses today.

## 3. The user picks what ships

Present one numbered list grouped by section, in the order [references/review-rubric.md](references/review-rubric.md) sets, each item showing current text → proposed text and the lens that motivated it. The user picks by number, all, or none. A rewrite that needs a fact nobody recorded earns one question at a time, and the answer appends to `career/career-diary.md`.

Done when: every numbered item carries a verdict — apply or skip.

## 4. Apply, one confirmed edit at a time

For each picked item, in order: show the section and old → new, ask for this edit's yes, then make that single edit in the browser and re-read the section to confirm it saved. Editing mechanics and field limits: [references/platform-notes.md](references/platform-notes.md).

Photo and cover-image changes ship as manual tasks for the user, with the rubric's guidance attached.

Done when: every picked item is saved-and-verified, declined at its own confirmation, or listed as a manual task.

## 5. Report and record

Report applied edits, declined items, and the manual tasks the user owns — photo, cover image, anything the platform will not let a browser session change. Everything not applied lands as a checklist in `<platform>/optimization-plan.md` (e.g. `linkedin/optimization-plan.md`); the report names it and says a second round scores the profile again once those items are done. Check off the `optimize-linkedin` stage in `.agents/state.md`, then commit the snapshot and the plan.

Done when: every unapplied item appears in the optimization plan, the plan and snapshot are committed, and the `optimize-linkedin` stage is checked off in `.agents/state.md`.
