---
name: interview
description: >-
  Prepare for one scheduled interview and debrief it afterwards — establish the
  format from the application record, research the company and the interviewers,
  build the question set and match it to the user's stories, rehearse on request,
  then capture what was asked and what it revealed. Use when an interview is
  scheduled or handed over by `inbox` or `track`, when the user asks to prep for
  an upcoming call, or when they report how an interview went. Moving the
  application's stage belongs to `track`; long-horizon technical preparation
  belongs to `teach`; reading recruiter threads belongs to `inbox`.
---

# Interview — prep and debrief

One application, one round. You prepare and you grade; the user answers and speaks. Relay facts inline in any prompt you write; `career/` and `applications.csv` stay in the main session.

**Prerequisites** — the application's row in `applications.csv` and its `job-descriptions/<stem>.md`. A company with no row hands off to `apply`, which logs it first.

**Two branches:**

- **Prep** — an interview is scheduled: steps 1–5.
- **Debrief** — the interview happened: steps 6–8.

One file per application, `interviews/<stem>.md`, holding every round in order: `## Round N — prep` written before the round, `## Round N — debrief` after it. A prep run appends to the same file it just read the last round's debrief out of.

## 1. Establish the format

The row's `notes` and `next_action` carry what was scheduled; `job-descriptions/<stem>.md` carries what the role demands. Name the format — recruiter screen, hiring-manager, technical, system design, panel, take-home, final — and ask the user when the invitation does not say, along with who is interviewing and how long the slot is.

Read every earlier debrief for this company first — the `## Round N — debrief` sections in `interviews/<stem>.md`, ids matched through `applications.csv`; the last round is the best available evidence for the next one. What each format tests, its question set, its method, and its bar: [references/interview-formats.md](references/interview-formats.md).

Done when: the format is named with what it tests, the interviewers are named or stated unknown, and every earlier debrief for this company has been read.

## 2. Research the company and the role

Delegate to a subagent, the JD snapshot and the format relayed inline in the prompt: the company as it stands today — recent news, funding, product line, engineering blog — the team and the role beyond the snapshot, and the public profile of each named interviewer. The subagent returns a brief; raw pages stay out of the main session.

Done when: the brief covers company, product, team, role, and each named interviewer, every claim carrying its source and its date.

## 3. Question set and stories

Build the likely-question set for this format from [references/interview-formats.md](references/interview-formats.md), weighted by the requirements the JD snapshot states and by anything an earlier debrief for this company recorded being asked.

Match each question to a story in `career/profile.md`, told as STAR. Where a question has no story behind it, say so plainly. That gap list is the highest-value output of the prep: it is what the user rehearses, what they decide to answer honestly, and what they may want to go and learn.

Done when: every question in the set carries a matched story or sits on the gap list.

## 4. Write the prep pack

Append `## Round N — prep` to `interviews/<stem>.md`, format: [references/pack-formats.md](references/pack-formats.md). The pack ends with the user's own questions for the interviewer, drawn from `goals/role-preferences.md` and `goals/search-filters.md` — what they still need to learn to judge an offer, filter by filter, plus anything the round is the only chance to ask. Comp, remote policy, and team size that `job-descriptions/<stem>.md` already answers stay out.

Done when: the round's prep section holds the format, the question set with its gaps, the matched stories, the research brief, and the user's questions, and the `interview` stage in `.agents/state.md` names the scheduled round.

## 5. Rehearse

Offer a mock loop; the user opts in. You ask one question per message, the user answers, and you grade that answer against the format's bar in [references/interview-formats.md](references/interview-formats.md) — what landed, what was missing, what to cut — then ask the next. Standard methods only: STAR for behavioural, a named framework for system design, think-aloud for coding.

Done when: the user has declined the mock loop or finished a round of it, and any answer that reshaped a story is back in the prep pack.

## 6. Walk it while it is fresh

One question per message, in order: what was asked, question by question; what went well; what went badly; what they could not answer; what they learned about the role, the team, and the company; their read on next steps and timing; and anything promised on either side — a take-home, a follow-up, a decision date.

Verbatim over paraphrase: the question as it was asked is what a prep run six weeks from now can use, and a summary of it is not.

Done when: every item above has the user's answer, and each question they could not answer is written down as it was asked.

## 7. Write the debrief and log the round

Append `## Round N — debrief` to `interviews/<stem>.md`, directly under this round's prep section, format: [references/pack-formats.md](references/pack-formats.md). Then hand the round to `track` as one event, so it moves the row's stage and the next action it created.

Done when: the round's debrief section exists and `track` has logged the round with its date, format, and outcome.

## 8. Route what it surfaced

Propose each route; the user picks. What they take is handed off in this run; what they decline is named once in the closing report and left there.

- A question they could not answer that names a real capability gap → say so, and offer `teach` for it: the user types `/teach <topic>` themselves, and it builds its workspace under `teach/<topic-slug>/`.
- An achievement they told well that is not yet recorded → append verbatim to `career/career-diary.md`, then hand to `highlights` for the bullet.
- Something learned about the company, the comp, or the role that changes what they want → `goals`.

Done when: every item from step 6 is routed, declined, or closed, and the `interview` stage in `.agents/state.md` names the round and its outcome.

## Commit

The prep pack and the debrief are the record of the round. After writing, offer to commit `interviews/`, `applications.csv`, and `.agents/state.md`.
