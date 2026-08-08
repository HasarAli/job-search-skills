# Stages

| Stage | Meaning |
|---|---|
| `applied` | submitted, no human response yet — an automated confirmation email does not advance the stage |
| `screen` | a human engaged: recruiter reply, screening call scheduled or done, assessment or take-home sent |
| `interview-N` | Nth round with the hiring team (N = 1, 2, 3…). The recruiter screen stays `screen`; a panel or onsite counts as one round |
| `offer` | offer extended, verbal or written |
| `rejected` | explicit rejection — the note records the stage it arrived at, e.g. "rejected after interview-2" |
| `ghosted` | silent past the ghost bar below, and the user chose to close it out |

`offer`, `rejected`, and `ghosted` are terminal: their rows leave the stale sweep.

## Transitions

- `applied → screen | rejected | ghosted`
- `screen → interview-1 | rejected | ghosted`
- `interview-N → interview-N+1 | offer | rejected | ghosted`
- `ghosted → screen | interview-N` — companies resurface; log the reopen as an event.

Those four lines, plus forward skips, are the full set: an event that lands past the next stage moves straight there — `applied` plus an onsite invite lands at `interview-1`, recording where reality is rather than the rung below it.

## Event → stage

| Event reported | New stage |
|---|---|
| Recruiter reply, screening call invited or completed, assessment or take-home received | `screen` |
| First interview with the hiring team, invited or completed | `interview-1` |
| A later round, invited or completed | N + 1 |
| Offer received, verbal or written | `offer` |
| Rejection at any point | `rejected` |
| User closes out a stale application | `ghosted` |
| Learning, note, thank-you sent, follow-up sent | unchanged |

Every event refreshes `last_activity`, `notes`, and the `next_action` pair, stage change or not.

## The ghost bar

Propose `ghosted` when both hold:

1. Silent for at least 2× `follow-up-days` since the last activity.
2. A follow-up went out, or the user declined to send one.

Set it once the user confirms.
