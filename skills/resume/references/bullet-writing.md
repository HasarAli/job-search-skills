# Bullet-writing rules

Applies to every highlight in `context/highlights.md` and every rewrite an advisor proposes. Pass this file's rules inline in advisor-subagent prompts.

## XYZ format

> **Accomplished [X] as measured by [Y] by doing [Z].**

- **X** — the outcome, leading with the product or business result, not the activity.
- **Y** — the measure: a number, percentage, time saved, revenue, scale, adoption.
- **Z** — the method: what the user actually did, with the concrete tools/approach.

Weak → strong:

- ✗ "Responsible for the reporting pipeline."
- ✗ "Rebuilt the reporting pipeline using new tooling." (activity, no outcome)
- ✓ "Cut monthly report turnaround from 5 days to 1 by rebuilding the reporting pipeline around automated data pulls."

The order can flex for readability (Z-first is fine when the outcome still lands early), but all three parts must be present. A bullet with no Y is a candidate for a metric question to the user, not for shipping.

## Skim test

Reviewers skim; the first pass is seconds per resume.

- **The first 3–5 words of each bullet must carry the value.** Front-load the outcome or the strongest verb+object. If the first line were truncated mid-sentence, the reader should still know why the bullet matters.
- One idea per bullet. Split compound achievements.
- Keep bullets to 1–2 lines rendered. Three-line bullets get skipped.
- Within a role, order bullets most-impressive-first for the *target role*, unless the user's chosen order says otherwise.
- Vary opening verbs across a role's bullets — five bullets starting with "Led" read as padding.

## Tense and voice

- Start with a strong past-tense action verb for past roles; present tense is acceptable for ongoing responsibilities in the current role — be consistent within an entry.
- No first person ("I", "my"), no pronouns at all.
- Active voice only: "Reduced costs by..." not "Costs were reduced...".
- No "Responsible for", "Helped with", "Worked on", "Assisted in" — say what was done.
- Write like a human. Avoid AI-writing tells: em-dash overuse, rule-of-three lists, promotional adjectives ("cutting-edge", "seamless"), vague attributions, trailing "-ing" clauses, negative parallelism ("not X but Y"), and filler.

## Metric integrity

- **Every claim traces to a line in `context/profile.md` or `context/career-diary.md`.** If a bullet needs a fact that isn't recorded, ask the user, then record the answer in `career-diary.md` before using it.
- **The user's supplied numbers are accepted as-is** — write them in immediately; never demand justification or evidence.
- **Never invent, extrapolate, or "round up" a metric.** No number from the user means the placeholder (e.g. `{{METRIC: description}}`) stays in the bullet and is flagged in the final report — a visible placeholder is recoverable; a fabricated number is not.
- Treat a placeholder as a pending value, not a flaw — advisors must not score a bullet down for it or fill it in.
