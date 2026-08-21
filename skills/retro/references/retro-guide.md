# Retro — find the leak

## Delegate the crunching

One subagent, so the main context stays small. It reads `applications.csv` and the job descriptions in `job-descriptions/`, and returns the metrics below, the mined title/keyword/seniority lists, and any anomaly it hit. Comparing those lists against `goals/role-preferences.md` and `career/highlights.md` happens in the main session.

## Metrics

Compute each over the whole history and over the last `retro-every` applications — the recent batch shows whether things are improving.

| Metric | Formula |
|---|---|
| Response rate | reached `screen` or beyond ÷ total, excluding rows younger than `follow-up-days` (too fresh to count as silence) |
| Screen rate | same numerator ÷ resolved rows (terminal, or silent past `follow-up-days`) |
| Screen → interview | reached `interview-1`+ ÷ reached `screen` |
| Interview → offer | reached `offer` ÷ reached `interview-1` |
| Rejection/ghost split | terminal rows by `rejected` vs `ghosted` |

Present as a funnel — applied → screen → interview → offer — with counts and conversion percentages between stages.

Then split every metric by segment: title, seniority, source board. A 0% response rate on one title and 8% on another is a targeting answer, not a resume answer.

## Mined from the applied JDs

| Dimension | The question it settles |
|---|---|
| Titles | do the titles applied to match the target list in `goals/role-preferences.md`? |
| Keywords | do the recurring required skills appear in the shipped resume and `career/highlights.md`? |
| Seniority | is the user applying above, at, or below the positioning in `goals/role-preferences.md`? |

## The leak table

| Symptom | Leak | Consider |
|---|---|---|
| Responses below ~1/50 | resume or targeting never survives the first skim | rewrite bullets against the mined keywords (`highlights`), then re-render (`create-resume`); revisit targets or seniority (`goals`); widen filters when volume is also low |
| Screens, no interviews | positioning or screen performance | sharpen the positioning story (`goals`); name the recurring screen questions from the debriefs in `interviews/` and hand them to `interview` |
| Interviews, no offers | loop performance | diagnose the round below |
| Ghosts concentrated in one source | board or channel quality | deprioritize that source in `.agents/search/config.yaml` (`search`) |

The ~1/50 mark opens a review, never a change: benchmarks move with industry, country, and market cycle. Present the numbers and the options; the user picks the one variable that changes.

## Diagnosing a failing loop

Name the round that fails from the debriefs in `interviews/<stem>.md` and the `notes` on each row, then hand the remedy to its owning skill. Every candidate fact a remedy leans on traces to a line in `career/profile.md` or `career/career-diary.md`; where the source is silent, getting it from the user comes first.

| Round | Signature in the notes | Remedy | Owner |
|---|---|---|---|
| Coding / technical screen | ran out of time, missed edge cases, silent while solving | timed practice at medium difficulty, solved out loud | `teach` |
| System design | interviewer drove, breadth without depth, requirements and trade-offs never stated | one system per week end-to-end: requirements → constraints → trade-offs → a deep dive on the hard part | `teach` |
| Behavioral | "we" instead of "I", no real conflict or stakes, story stops before the outcome | rewrite the three weakest STAR stories from the raw notes in `career/career-diary.md` — own actions, real conflict, measured outcome. With no story bank in `career/profile.md` yet, building one with the user comes first | `highlights` |
| Final / hiring manager | verdict came back as a down-level, or the conversation stalled on comp | recalibrate the target level, and rehearse the base-comp floor from `goals/search-filters.md` as the opening number | `goals` |

## The noise floor

- Under ~20 resolved applications, conversion rates are noise. Report them, and change only what is plainly broken — wrong resume attached, dead link.
- Late-stage rates need late-stage volume: at 2 interviews, an interview→offer of 0% is noise, and saying so beats prescribing prep.
- Change one variable at a time, then measure the next batch against the previous one — simultaneous changes make the next retro uninterpretable.

## Close

Report the findings and the agreed actions to the user, and hand each action to its owning skill with the finding that motivated it. The routing table is in `SKILL.md` step 3.
