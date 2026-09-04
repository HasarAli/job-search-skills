---
name: apply
description: >-
  Apply to job postings and record every application: autofill the form, answer
  questions from the Q&A bank, create a draft application record, get the user's
  explicit yes before each submit, then advance that record to `applied`. Use when the user says "apply
  to jobs", "apply to 1 and 3", or wants an already-submitted role logged in the
  tracker — inbound from a recruiter, or one they sent themselves outside this
  skill. What happens after a submit — replies, interviews, follow-ups — belongs
  to `track`; reading recruiter threads belongs to `inbox`; rendering the resume
  PDF belongs to `create-resume`.
---

Relay facts inline in any prompt you write; the candidate documents and `search/applications/index.csv` stay in the main session.

**Prerequisites** — read `.agents/state.md` for the other stages. Applying from a shortlist reads the newest `search/shortlists/*.md` (the latest run); with none present, hand off to `script-search`.

**Two branches:**

- **Submit** — the user picks postings to apply to: steps 1–5.
- **Log** — the application already went out (an inbound role handed over by `inbox`, or one the user sent themselves): ask how the role arrived, obtain the exact submitted resume and what stands in for the posting — its text, an attached JD, or the recruiter message itself — create the application directory and draft row, then run steps 4 and 5. The row's `source` and `notes` carry how the role arrived and where it already stands.

Steps 2–4 run one application at a time: the next posting opens only after this one is recorded.

## 1. Selection and pre-batch check

Read the shared [shortlist format](../../search/shortlist-format.md) for run filenames and selection rules; both search skills produce this format.

Selection is the shortlist entries the user names, by number or company (`apply 1 3 5`). Use the shortlist explicitly referenced in the conversation, otherwise the latest run by filename timestamp and collision suffix, not modification time. A full timestamp or filename selects a specific run; a date matching multiple runs requires asking which one. For ambiguous legacy names, consult the file's recorded run time or ask. Confirm the filename and selected companies before opening postings; row numbers are local to that file. With nothing named, show the shortlist and ask which entries.

`.agents/config/autofill-config.json` missing → offer autofill setup before the batch: [references/autofill-setup.md](references/autofill-setup.md). `"service": "none"` is a complete config, and every field then comes from the bank and the user's answers.

Choose the matching current base under `search/resumes/<role-slug>/<region>/`. Allocate the application stem, create `search/applications/<stem>/`, save the posting as `job-description.md`, and create its index row with `status: draft`. Compare the job description with the base and recommend tailoring only when the differences are material; if the user chooses it, hand the application directory to `create-resume`.

Copy the selected or tailored YAML into the application directory and name it `<First>_<Last>_<Posted_Role>_Resume.yaml`. Render the matching PDF there for review and attachment, but leave `resume_file` empty while the row is a draft. Compare `.agents/config/autofill-config.json`'s `resume_file` with that application-local PDF: the service attaches whatever was last uploaded to it, so any mismatch must be resolved or explicitly confirmed before filling.

Done when: every selected entry has an application directory with `job-description.md`, an application-local YAML and rendered PDF, a `draft` index row, `.agents/config/autofill-config.json` exists, and the PDF the service will attach is confirmed to be that application-local file.

## 2. Open and fill

Open the posting with whatever browser-automation tools this harness provides, driving the user's own signed-in session; an expired session ends the run — report it and stop there. Trigger the configured autofill service, then close the remaining fields from `.agents/config/qa-bank.md`, matching on meaning rather than wording: [references/qa-bank-format.md](references/qa-bank-format.md). Attach the application-local PDF. When an autofill service attaches its stored file, confirm that file is the same resume before continuing.

Anything the bank cannot answer is one question to the user per message, and their answer is what goes in the field.

Done when: every field holds a value from the candidate documents, the bank, or the user; the application-local PDF is attached; and any field left blank is named to the user.

## 3. Submit gate

Show the finished application field by field — every answer as it will be sent, plus the resume filename — and ask for a yes for this application. Submit on that yes. Each yes is single-use: it covers this application and no other.

Done when: the user's yes for this application is in the transcript above the submit click.

If the user declines or submission cannot proceed, leave the application directory and its `draft` row in place. Record the blocker or decision in `notes` and set the next action; a later run resumes the same application.

## 4. Record

Four records, all complete before the next posting opens. Formats: [references/record-format.md](references/record-format.md).

- the existing row in `search/applications/index.csv`, changed from `draft` to `applied`, whose `resume_file` is now the relative path to the application-local PDF and whose `next_action` pair holds what happens next
- `search/applications/<stem>/job-description.md`, saved before submission as the posting stood
- the exact submitted YAML and PDF under `search/applications/<stem>/`
- new Q&A pairs appended to `.agents/config/qa-bank.md`, so the next form has fewer gaps

Delegate the JD snapshot to a subagent to keep the raw source out of the main context: the prompt carries the source text — posting, attached JD, or recruiter message — the subagent returns the snapshot, and requirements, responsibilities, comp and location survive verbatim.

Done when: the row carries its application-local `resume_file` and a `next_action` with its date, the application directory contains `job-description.md` plus the exact submitted PDF and YAML, and every new answer is in the bank.

## 5. Close the batch

Report per application: id, company, role, application directory, exact resume attached, and anything the user still owes an answer on. Outstanding items are said to the user here and nowhere else — no file collects them. Update the `apply` stage in `.agents/state.md` with the new total.

Done when: every selected entry appears in the report as submitted-and-recorded or as skipped with its reason, and `.agents/state.md` names the new total.
