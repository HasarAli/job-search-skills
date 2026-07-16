---
name: profile
description: Audit, review, and optimize the user's professional profile (LinkedIn or another platform). Use when asked to audit, review, improve, or optimize their LinkedIn or professional profile, headline, About section, or profile settings.
---

# Profile — audit + optimize the user's professional profile

Crawl the user's own profile on their logged-in browser session, have advisor agents
review it section by section, then apply the edits the user approves — one at a time,
each individually confirmed.

## Prerequisites

- `state.md` shows onboarding complete (through `onboard:advisors`). If not, stop and
  point the user at the `onboard` skill.
- Platform comes from `search/search-config.md`; default is LinkedIn. Browser tools must
  reach the user's logged-in session — if not logged in, ask the user to log in first.

## Flow

### 1. Crawl (subagent)

Spawn one subagent to crawl the profile with browser tools and write a structured
snapshot report under the data repo at `context/<Platform>/YYYY-MM-DD/report.md` (e.g.
`context/LinkedIn/2026-07-09/report.md`). What to capture per section and the report
structure: `references/crawl-guide.md`. Crawl gently, the user's own profile only. The
subagent returns the report path plus a short summary; the main session does not hold
the raw crawl.

### 2. Review (advisor subagents)

Spawn advisor subagents — at minimum `profile-platform-expert` and `recruiter-reviewer`
— by reading each one's `advisors/<name>.md` from the data repo and inlining its full
contents as that subagent's persona prompt (no agent-registry lookup), plus the snapshot
report path. Each reviews section by section (headline, about, experience, skills,
featured, settings, ...) and returns scored findings and concrete rewrite suggestions.
Advisors review and suggest; they never edit anything. Write each advisor's full review
to `context/<Platform>/YYYY-MM-DD/reviews/<advisor-name>.md` (gitignored — raw review
transcripts, not synthesized context). Platform-specific review angles:
`references/platform-notes.md`.

### 3. Recommend (main session)

Consolidate the advisors' findings into one numbered recommendation list, grouped by
section, each item showing current text → proposed text and a one-line reason. Present
it and let the user pick which recommendations to apply (all / numbers / none). Where
findings need facts only the user has, ask one question at a time.

### 4. Apply (one edit at a time)

For each approved edit, in order:

1. Show exactly what will change (section, old → new).
2. Ask for explicit confirmation of THIS edit. No batch approval — step 3's selection
   chooses candidates; each edit still gets its own yes before the browser touches it.
3. On yes, make the single edit via browser automation on the logged-in session, then
   verify it saved before moving to the next.

Profile photo and cover image changes are never automated — flag them as manual tasks
for the user with the advisors' guidance attached.

### 5. Wrap up

Summarize applied edits and remaining manual tasks. Update `state.md` (`profile` stage
done). Commit the snapshot report and any notes to the data repo.

## References

- `references/crawl-guide.md` — sections to capture, snapshot report format, crawl cautions.
- `references/platform-notes.md` — LinkedIn specifics, Xing notes, generic-platform fallback.
