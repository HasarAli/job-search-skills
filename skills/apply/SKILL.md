---
name: apply
description: >-
  Apply to job postings and record every application: autofill the form, answer
  questions from the Q&A bank, get the user's explicit yes before each submit,
  then write the application into `applications.csv`. Use when the user says "apply
  to jobs", "apply to 1 and 3", or wants an already-submitted role logged in the
  tracker — inbound from a recruiter, or one they sent themselves outside this
  skill. What happens after a submit — replies, interviews, follow-ups — belongs
  to `track`; reading recruiter threads belongs to `inbox`; rendering the resume
  PDF belongs to `resume`.
---

Relay facts inline in any prompt you write; `career/`, `goals/` and `applications.csv` stay in the main session.

**Prerequisites** — read `.agents/state.md`. Applying from a shortlist needs `shortlists/<YYYY-MM-DD>.md`; with none present, hand off to `search`.

**Two branches:**

- **Submit** — the user picks postings to apply to: steps 1–5.
- **Log** — the application already went out (an inbound role handed over by `inbox`, or one the user sent themselves): ask the user how the role arrived, which resume went out, and what stands in for the posting — its text, an attached JD, or the recruiter message itself — then steps 4 and 5 alone, with the row's `source` and `notes` carrying how the role arrived and where it already stands.

Steps 2–4 run one application at a time: the next posting opens only after this one is recorded.

## 1. Selection and pre-batch check

Selection is the shortlist entries the user names, by number or company (`apply 1 3 5`), from today's shortlist `shortlists/<today>.md`; a `YYYY-MM-DD` argument picks an older one. With nothing named, show the shortlist and ask which entries.

`.agents/config/autofill-config.json` missing → offer autofill setup before the batch: [references/autofill-setup.md](references/autofill-setup.md). `"service": "none"` is a complete config, and every field then comes from the bank and the user's answers.

Compare the config's `resume_file` against the newest matching render under `resumes/<YYYY-MM-DD>/` and put any mismatch to the user — the service attaches whatever was last uploaded to it. With no matching render on disk (a fresh clone renders nothing), ask whether the resume the service holds is still the current one.

Done when: every selected entry has a posting URL, `.agents/config/autofill-config.json` exists, and the resume the service will attach is either confirmed current or flagged to the user.

## 2. Open and fill

Open the posting with whatever browser-automation tools this harness provides, driving the user's own signed-in session; an expired session ends the run — report it and stop there. Trigger the configured autofill service, then close the remaining fields from `.agents/config/qa-bank.md`, matching on meaning rather than wording: [references/qa-bank-format.md](references/qa-bank-format.md). Attach the resume named in `autofill-config.json`, or the newest matching render under `resumes/<YYYY-MM-DD>/` when the service is `none`.

Anything the bank cannot answer is one question to the user per message, and their answer is what goes in the field.

Done when: every field holds a value from the bank, a `career/` or `goals/` doc, or the user, and any field left blank is named to the user.

## 3. Submit gate

Show the finished application field by field — every answer as it will be sent, plus the resume filename — and ask for a yes for this application. Submit on that yes. Each yes is single-use: it covers this application and no other.

Done when: the user's yes for this application is in the transcript above the submit click.

## 4. Record

Three writes, all before the next posting opens. Formats: [references/record-format.md](references/record-format.md).

- a row in `applications.csv`, `status: applied`, with `next_action` and `next_action_date` holding what happens next — the follow-up date when the ball is the company's
- `job-descriptions/<stem>.md` — the job description as it stood, and nothing the row already carries
- new Q&A pairs appended to `.agents/config/qa-bank.md`, so the next form has fewer gaps

Delegate the JD snapshot to a subagent to keep the raw source out of the main context: the prompt carries the source text — posting, attached JD, or recruiter message — the subagent returns the snapshot, and requirements, responsibilities, comp and location survive verbatim.

Done when: the row carries a `next_action` with its date, `job-descriptions/<stem>.md` exists, and every new answer is in the bank.

## 5. Close the batch

Report per application: id, company, role, resume attached, and anything the user still owes an answer on. Outstanding items are said to the user here and nowhere else — no file collects them. Update the `apply` stage in `.agents/state.md` with the new total, then offer to commit `applications.csv`, `job-descriptions/`, `.agents/config/qa-bank.md` and `.agents/state.md` — the batch's writes are the audit trail.

Done when: every selected entry appears in the report as submitted-and-recorded or as skipped with its reason, `.agents/state.md` names the new total, and the commit offer is with the user.
