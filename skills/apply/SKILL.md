---
name: apply
description: Apply to jobs from a shortlist — autofill each application, answer questions from the Q&A bank, get explicit human approval before any submit, then record everything. Use when asked to "apply to jobs", "apply to 1 3 5", "submit applications", or "apply from the shortlist".
---

# Apply — autofill → human-approved submit → record

## Args

- Shortlist item numbers, e.g. `apply 1 3 5`. Default source: today's `search/shortlists/shortlist-YYYY-MM-DD.md`.
- Optional date arg (`YYYY-MM-DD`) selects an older shortlist.
- No numbers given → show the shortlist and ask which to apply to.

Check `state.md` first. If no shortlist exists, point the user at the `search` skill.

## First run

If `applications/autofill-config.md` does not exist, offer (optional) autofill-service
setup before applying — Simplify is the default adapter, but any service or none is
fine. Walkthrough: `references/autofill-setup.md`. Skipping is allowed; fields are
then filled manually from the Q&A bank.

## Per-job loop

For each selected shortlist item:

1. **Open** the posting in the user's browser (browser tools, their logged-in session).
2. **Autofill** — trigger the configured autofill service on the application form.
3. **Fill gaps** from `applications/qa-bank.md` (see `references/qa-bank-format.md` for
   matching guidance — same question, different phrasing).
4. **New questions** — for anything the bank can't answer, ask the user in the main
   session, one question at a time. Never invent an answer.
5. **NEVER SUBMIT WITHOUT PERMISSION.** Present the completed application (every field
   and answer as filled) and ask for explicit permission for THIS application. Only on
   the user's yes, click submit. A yes for one application never carries to the next.
6. **Record immediately** after submit (before opening the next job).

## Record (per submitted application)

Formats and templates: `references/record-format.md`.

- Append a row to `applications/applications.csv`:
  `id, datetime, company, role, location, source, url, resume_file, status, last_activity, notes`
- Write `applications/<id>.md`: JD snapshot text, resume filename used, every ad-hoc
  answer given during this application.
- Append any new Q&A pairs to `applications/qa-bank.md` — the bank compounds and
  shortens every future application.

Update `state.md` (`apply` stage) when the batch completes.

## Orchestration

Browsing, form-filling, and permission asks are inherently main-session work — they
need the user's browser and per-application confirmations. Delegate JD snapshot
summarization (raw posting text → snapshot for `<id>.md`) to a subagent.
