# channels.md — schema and seed

> A **seed**: copied once into `.agents/config/channels.md`, which is where every later
> channel section lives. A skill update overwrites this file.

One `##` section per configured channel — that list is what `inbox` sweeps. A platform
with no section there is not a channel yet. Onboarding procedure:
[boards.md](boards.md#onboarding-an-inbox-channel).

## Seed

```markdown
# Inbox Channels

One `##` section per configured channel — that list is what `inbox` sweeps. Each section
holds the entry URL, how to open a thread, how to extract a body, and what to skip.
Maintained by the `sources` skill; corrected in place by `inbox` when a step no longer
matches the screen.

## <Platform>

### Entry

`<URL the sweep starts from>`

<Any query param or redirect that has to survive navigation — a filter that separates
recruiter mail from ordinary messages, an account index that redirects, a load delay
long enough to look like a dead session.>

### Open a thread

<Which element accepts the click and which one silently does nothing: the row, the card
inside it, a coordinate. How threads collapse or group, and how to expand an older
message inside one.>

### Extract

<What the harness's page-text extraction returns for an open thread — the whole thread,
or only the list. Where the thread starts in that output, and what to skip past. If the
body renders in an iframe or a canvas, say so: that channel needs a screenshot per
message, not a text extract.>

### Reading the list

<How many threads load before scrolling, where "load more" sits, and what the list
preview does and does not show — a preview that shows only the subject line makes an
answered thread look identical to an unanswered one.>

### Finding a thread

<How to search by company name, whether search covers sent mail and archives, and what
it excludes by default.>

### Skip

<What dominates this channel by volume and is never worth reading: job alerts,
notification mirrors of messages already read elsewhere, transactional mail.>

### Signals

<What the platform's own labels mean — a sender name that marks a restricted account, a
subject line that names the company versus one that withholds the client.>

### High-value content

<What is worth more than the message body: calendar invitations carrying a time already
converted to the user's timezone, an RSVP row still showing buttons (the invitation is
unanswered), attachment filenames.>

### Guardrails

<Every action that is the user's own click and never the agent's: sending, replying,
forwarding, accepting a request, RSVPing, opening a scheduling link. Report the link and
let the user act.>
```

## Filling it

Write a section only from what was observed in the user's own browser — one message list
opened, one thread opened, one body extracted. A heading with nothing observed under it
is dropped rather than guessed at; the headings above are the full menu, not a checklist.

Record what surprised you. The value of a section is the thing that is not obvious from
looking at the page: which element the click lands on, whether extraction returns the
thread or only the list, whether the body needs a screenshot, how to filter the list down
to recruiter mail.
