# Application Record Format

The record of an application is its row in `applications.csv`. The posting it was for is `job-descriptions/<stem>.md`. Nothing else is written per application.

## File names

Every file belonging to one application shares one **stem** — `<id>-<company>-<role>` — so the row, the posting, and the interview notes line up on sight:

```
2026-07-28-01-acme_corp-senior_software_engineer.md
└── date ──┘ │ └─ company ──┘ └────── role ──────────┘
             └─ which application that day
```

Dashes separate the parts, underscores hold each part together, and nothing is shortened. `job-descriptions/<stem>.md` holds the posting; `interviews/<stem>.md` holds every round (format: interview's [pack-formats.md](../../interview/references/pack-formats.md)).

## applications.csv

Header line (create the file with it if missing):

```csv
id,datetime,company,role,location,source,url,resume_file,status,last_activity,notes,next_action,next_action_date
```

| Column | Definition |
|---|---|
| `id` | `YYYY-MM-DD-NN` — submission date plus a two-digit sequence within that day from `01` (`2026-07-14-03` = third application on 2026-07-14). Get `NN` by counting existing rows with the same date prefix |
| `datetime` | Submission time, ISO 8601 local (`2026-07-14T15:32`) |
| `company` | Company name as posted |
| `role` | Job title as posted |
| `location` | Location string from the posting (city/remote/hybrid) |
| `source` | Where the job came from — the board or platform name from the shortlist entry, or the inbound channel and the recruiter's name |
| `url` | Posting URL; left empty when a recruiter supplied the role directly |
| `resume_file` | Full filename of the resume attached |
| `status` | `applied` at creation; later transitions belong to `track` |
| `last_activity` | Date of the most recent event (`2026-07-14`) — the submission date at creation, moved by `track` |
| `notes` | Where this application stands, in free text: who is handling it, what was scheduled and when, referral, filter tension, anything learned. Rewritten each time it changes, not appended to |
| `next_action` | The single move that comes next and whose it is — "send thank-you note to Catherine", "await recruiter reply", "RSVP the calendar invite". Empty once `status` is terminal |
| `next_action_date` | Date `next_action` is due or expected (`2026-08-11`). Empty when `next_action` is |

Fields containing commas are quoted. One row per application: every event edits that row rather than adding another, and `next_action` plus `next_action_date` are the pair the user is asking about whenever they ask where things stand.

The row holds the present, not the past. History is in git — `git log -p applications.csv` replays every status, note, and action with the date it changed, which is why the tracker gets committed after each write.

## job-descriptions/&lt;stem&gt;.md

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
