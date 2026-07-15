# Application Record Format

Two artifacts per submitted application: a CSV row (the tracking index, consumed by the `track` skill) and a per-application markdown file (the detail record). Write both immediately after submit, before opening the next job.

## applications.csv

Header line (create the file with this line if missing):

```csv
id,datetime,company,role,location,source,url,resume_file,status,last_activity,notes
```

| Column | Definition |
|---|---|
| `id` | Unique application id, see scheme below |
| `datetime` | Submission time, ISO 8601 local (`2026-07-14T15:32`) |
| `company` | Company name as posted |
| `role` | Job title as posted |
| `location` | Location string from the posting (city/remote/hybrid) |
| `source` | Where the job was found (board/platform name from the shortlist entry) |
| `url` | Posting URL |
| `resume_file` | Full filename of the resume attached/used |
| `status` | Lifecycle stage; always `applied` at creation. Later transitions owned by the `track` skill |
| `last_activity` | Date of the most recent event, ISO 8601 (`2026-07-14`). Set to the submission date at creation; updated by the `track` skill on every event |
| `notes` | Short free text (referral, salary stated, anything notable); empty is fine |

Quote fields containing commas. One row per application; rows are append-only — status updates edit the existing row (via `track`), never add duplicates.

## id scheme

`YYYYMMDD-NN` — submission date + two-digit sequence within that day, starting at `01` (e.g. `20260714-03` = third application on 2026-07-14). Determine `NN` by counting existing rows with the same date prefix.

## <id>.md template

Path: `applications/<id>.md`.

```markdown
# <company> — <role>

- id: <id>
- applied: <datetime>
- url: <posting url>
- resume: <resume_file>

## JD snapshot

<Text snapshot of the job description as posted — postings vanish; this is the
durable copy. A subagent may summarize long postings, but keep requirements,
responsibilities, and comp/location details verbatim enough to prep interviews from.>

## Answers given

<Every ad-hoc answer supplied during this application — question, then the answer
as submitted. Empty section if autofill + qa-bank covered everything.>

## Notes

<Optional: referral, hiring manager name, anything learned during the apply.>
```

New Q&A pairs from "Answers given" are also appended to `qa-bank.md` (see `qa-bank-format.md`) — the `<id>.md` copy is the historical record of what this application actually said.
