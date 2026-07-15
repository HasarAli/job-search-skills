# Stage taxonomy

`applied → screen → interview-N → offer | rejected | ghosted`

## Definitions

| Stage | Meaning |
|---|---|
| `applied` | Application submitted; no human response yet. Automated confirmation emails do not advance the stage. |
| `screen` | A human engaged: recruiter reply, screening call scheduled or done, take-home/assessment sent. |
| `interview-N` | Nth interview round with the hiring team (N = 1, 2, 3…). The recruiter screen is `screen`, not `interview-1`. Panels/onsites count as one round. |
| `offer` | Offer extended (verbal or written). |
| `rejected` | Explicit rejection at any point. Record the stage it arrived at in the note (e.g. "rejected after interview-2"). |
| `ghosted` | No response past the ghosted threshold; user chose to close it out. |

Terminal stages: `offer`, `rejected`, `ghosted`. Terminal rows are excluded from follow-up flagging.

## Valid transitions

- `applied → screen | rejected | ghosted`
- `screen → interview-1 | rejected | ghosted`
- `interview-N → interview-N+1 | offer | rejected | ghosted`
- `ghosted → screen | interview-N` — reopening is valid; companies do resurface. Log the reopen event.
- Never move backward otherwise. If an event seems to skip a stage (e.g. straight from `applied` to an onsite invite), skip forward — record reality, not the ideal ladder.

## Event → stage mapping

| Event reported | New stage |
|---|---|
| Recruiter reply, screening call invite/completed, assessment or take-home received | `screen` |
| Interview invite/completed with hiring team (first) | `interview-1` |
| Subsequent interview round invite/completed | increment N |
| Offer received (verbal or written) | `offer` |
| Rejection email/call at any point | `rejected` |
| User closes out a stale application | `ghosted` |
| Learning, note, thank-you sent, follow-up sent | stage unchanged — event note only; resets the activity clock |

Every event, stage-changing or not, gets a dated note in `applications/<id>.md` and updates the row's `last_activity` column.

## Ghosted criteria

Mark `ghosted` only when all three hold:

1. No response for at least 2× `follow-up-days` (default: 28 days) since the last activity.
2. At least one follow-up was sent (or the user explicitly declines to follow up).
3. The user confirms — never auto-ghost; the skill proposes, the user decides.
