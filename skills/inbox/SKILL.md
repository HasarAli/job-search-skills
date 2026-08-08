---
name: inbox
description: >-
  Triage inbound recruiter messages — read new threads on each configured
  channel, score them against the search filters, and report what is scheduled,
  what needs a reply, and what has gone silent. Use when the user asks to check
  their inbox, messages, or whether a recruiter has reached out, or names a
  platform to focus the sweep on or add to it. Outbound applications belong to
  `apply`; logging what an inbound thread reports belongs to `track`; adding a
  new channel belongs to `sources`.
---

Inbound only. You read, score, and recommend; the user sends every reply.

**Prerequisites** — `.agents/state.md` for the last sweep date. A missing `goals/search-filters.md` hands off to `goals`.

**Channels** — read `.agents/config/channels.md`: one `##` section per configured channel, holding its entry URL, how to open a thread, how to extract a body, and what to skip. Those sections are the channel list. A platform the user names with no section there gets onboarded by `sources` first.

## 1. Read

Sweep every channel unless the user names one. Follow each guide newest-first, back to the last sweep date in `.agents/state.md` — 3 weeks on a first run.

Read with whatever browser-automation tools this harness provides, driving the user's own signed-in session. An expired session ends that channel's sweep: name the channel and move on.

Reading marks threads read — say so before you start.

Where a guide's steps no longer match the screen, correct the guide in place as you go. A guide that has drifted costs a round of flailing every run.

Match threads by company name across channels before calling one silent. A LinkedIn thread often continues over email, and the newest message sits on whichever platform it moved to.

Done when: every swept channel has been followed to its cut-off date, and each company appears once, with the newest message across channels identified.

## 2. Triage

Score every thread against `goals/search-filters.md` and `goals/role-preferences.md`, naming the filter it clears or breaks. Overrides are the user's call, so a thread that breaks one still reaches the report, gap stated.

Low signal: the client company withheld, an email address or phone number asked for before any JD, an account that cannot receive replies. Contact details are the user's to give — relay the request, never the data.

Done when: every thread read carries a verdict — clears, breaks a named filter, or low-signal.

## 3. Report

One report across all channels. Sections in order:

1. **Live pipeline** — a scheduled call, a decision pending from the company, or a resume already sent. Table: thread, status, next action + date, channel to reply on.
2. **Needs a decision** — awaiting the user's reply. One line each: the filter verdict, then your recommendation.
3. **Filter mismatches** — live threads breaking a stated filter. Name the filter and the gap once.

Then one line each for threads correctly closed, and for threads silent past the follow-up cadence in `goals/search-filters.md` — dead, or due a nudge.

Scheduling detail is the highest-value output: date, time in the user's own timezone (region in `goals/search-filters.md`), who calls whom on what number, and whether the invitation is still unanswered.

Drafting a reply on request is welcome. Sending, replying, and answering an invitation are the user's own clicks.

Done when: every triaged thread sits in exactly one section, and every scheduled call states its time in the user's timezone plus its RSVP state.

## 4. Hand off

- Inbound role absent from `applications.csv` → `apply` logs it; inbound belongs in the tracker too.
- A recruiter reply, rejection, interview invitation, or outcome on a tracked application → `track` logs it as an event, carrying the thread's own wording; the next action this report names for that thread is what lands on the row.

Done when: the `inbox` stage in `.agents/state.md` records today's sweep date and the channels swept, and each hand-off above has been taken or named to the user.
