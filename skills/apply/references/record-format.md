# Application Record Format

The application index is `search/applications/index.csv`. Every application has one directory from preparation onward, containing the posting, resume source, the exact submitted PDF once sent, and its interview record when one exists.

## File names

Every application directory has one **stem** — `<id>-<company>-<role>` — so the row and its files line up on sight:

```
search/applications/2026-07-28-01-fitch_ratings-senior_software_engineer/
└── date ──┘ │ └─ company ──┘ └────── role ──────────┘
             └─ which application that day
```

Dashes separate the stem's parts, underscores hold words inside a part together, and nothing is shortened. The directory contains:

```
job-description.md
<First>_<Last>_<Posted_Role>_Resume.yaml
<First>_<Last>_<Posted_Role>_Resume.pdf              # once submitted
interview.md                                      # once interview work begins
```

Resume filenames contain no company, date, region, version number, or `final`; the directory carries that identity. The PDF is the exact file submitted, even when it was copied unchanged from a base resume. The YAML is the matching source. Interview format: [pack-formats.md](../../interview/references/pack-formats.md).

## search/applications/index.csv

Header line (create the file with it if missing):

```csv
id,datetime,company,role,location,source,url,resume_file,status,last_activity,notes,next_action,next_action_date
```

| Column | Definition |
|---|---|
| `id` | `YYYY-MM-DD-NN` — application workspace creation date plus a two-digit sequence within that day from `01`. For an already-submitted application being logged later, use its submission date. |
| `datetime` | Application workspace creation time, ISO 8601 local (`2026-07-14T15:32`); for historical records, use the most precise known submission date or time without inventing precision. |
| `company` | Company name as posted |
| `role` | Job title as posted |
| `location` | Location string from the posting (city/remote/hybrid) |
| `source` | Where the job came from — the board or platform name from the shortlist entry, or the inbound channel and the recruiter's name |
| `url` | Posting URL; left empty when a recruiter supplied the role directly |
| `resume_file` | Empty while `draft`; project-relative path to the exact local application PDF once attached and submitted. The PDF is ignored; only its YAML source is committed. |
| `status` | `draft` at workspace creation; `applied` only after submission; later transitions belong to `track` |
| `last_activity` | Date of the most recent event (`2026-07-14`) — workspace creation for a draft, then submission and later events |
| `notes` | Where this application stands, in free text: who is handling it, what was scheduled and when, referral, filter tension, anything learned. Rewritten each time it changes, not appended to |
| `next_action` | The single move that comes next and whose it is — "send thank-you note to Catherine", "await recruiter reply", "RSVP the calendar invite". Empty once `status` is terminal |
| `next_action_date` | Date `next_action` is due or expected (`2026-08-11`). Empty when `next_action` is |

Fields containing commas are quoted. One row per application: every event edits that row rather than adding another, and `next_action` plus `next_action_date` are the pair the user is asking about whenever they ask where things stand.

The row holds the application's current state; no separate event log is maintained.

## search/applications/&lt;stem&gt;/job-description.md

The job description as it stood, and nothing else — postings vanish, and this is what `interview` and `apply` read to know what the role actually asked for. Anything that is already a CSV column stays out.

```markdown
# <company> — <role>

<Where the description came from and when: the posting URL, an attached JD named by
its filename, or the recruiter message it was pulled from.>

<The description itself, verbatim enough to prep an interview from: requirements,
responsibilities, stack, team, comp, location. Where the outreach carried no
description, one line saying so is the whole file.>
```

Answers the form asked for do not live here: the reusable pattern behind each one goes to `.agents/config/qa-bank.md` ([qa-bank-format.md](qa-bank-format.md)), and a one-off answer worth remembering goes in `notes`.
