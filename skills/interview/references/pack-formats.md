# Prep Pack and Debrief Formats

One file per application, `interviews/<stem>.md` — the same stem the row and the posting carry, defined in apply's [record-format.md](../../apply/references/record-format.md) — holding the rounds in the order they happened: `## Round N — prep` written before the round, `## Round N — debrief` after it. A new round appends its prep section to the bottom.

The file opens with the header block, written once on the first round:

```markdown
# <company> — <role>

- id: <id>
- rounds: <one line per round as it is scheduled: `1 — technical, 2026-08-14`>
```

## `## Round N — prep`

```markdown
## Round <N> — prep

- format: <recruiter screen | hiring-manager | technical | system design | panel | take-home | final>
- scheduled: <YYYY-MM-DD HH:MM, user's timezone>
- interviewers: <name — title, and what their public profile says they will probe; or `unknown`>
- length: <minutes>

### Company brief

<From step 2's subagent, each claim with its source and date: what the company
does, recent news and funding, the product line, what the engineering blog says
about the stack and how they work. Facts only — no adjectives.>

### Role brief

<What this role demands beyond `job-descriptions/<stem>.md`: the team it sits on, who it reports
to, what the stated requirements imply about the first six months.>

### Question set

<One subsection per likely question, ordered most to least likely:

#### <the question, as an interviewer would ask it>

**Story:** <which story from `career/profile.md`, told as STAR — Situation, Task,
Action, Result, with the number the profile records.>
>

### Gaps

<Every question in the set with no story behind it, one bullet each: the question,
what an answer would need, and the honest position the user can take instead.
This is the list the user rehearses. A gap that names a real capability gap is a
`teach` hand-off, marked here as one.>

### Questions for the interviewer

<What the user still needs to learn to judge an offer, drawn from `goals/`. One
bullet each: the question, and the filter or preference it settles.>
```

Earlier rounds need no summary section: they sit in this same file, directly above.

## `## Round N — debrief`

Written from the user's own account, in their words. Verbatim beats summary: a prep run months later can use the question as it was asked and cannot use a paraphrase of it.

```markdown
## Round <N> — debrief

- held: <YYYY-MM-DD>
- interviewers: <names and titles as they introduced themselves>
- outcome: <advanced | rejected | waiting — decision expected <date> | unknown>

### What was asked

<Every question the user recalls, verbatim, one bullet each, with a one-line note
on how they answered.>

### Went well

<What landed, and why the user thinks it landed.>

### Went badly

<What did not land, in their words.>

### Could not answer

<One bullet per question with no answer: the question verbatim, and whether it is
a capability gap (`teach`), a story that exists but was not reached for, or a
company fact nobody could have known.>

### Learned about the role

<Team, stack, scope, comp, process, timeline — anything `job-descriptions/<stem>.md` did not say.
What changes the user's read on the offer goes to `goals`.>

### Read on next steps

<What the interviewer said about timing and next rounds, what the user owes them,
and by when. This is what `track` turns into the row's `next_action`.>

### Routed

<One line per item from the debrief and where it went: `teach`, `career/career-diary.md`
plus `highlights`, `goals`, or declined by the user.>
```
