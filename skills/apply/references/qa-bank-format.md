# Q&A Bank Format

`applications/qa-bank.md` is the reusable answer store for application-form questions (work authorization, salary expectations, notice period, "why us" patterns, relocation, start date, …). It compounds: every new answer given during an application is appended, so the bank covers more of each successive form.

## Structure

One entry per question pattern:

```markdown
## <Question pattern>

**Answer:** <canonical answer, as it should be typed into a form>

**Variants:** <other phrasings that mean the same question>
**Notes:** <when to deviate — e.g. per-country, per-role, or per-seniority adjustments>
```

Example:

```markdown
## Are you legally authorized to work in <country>?

**Answer:** Yes

**Variants:** "Do you have the right to work in…", "Work authorization status",
"Will you now or in the future require sponsorship?" (inverse — answer No)
**Notes:** Sponsorship questions are the inverted form; read carefully before reusing.
```

Group entries under top-level headers if the bank grows large (`# Eligibility`, `# Compensation`, `# Motivation`), but flat is fine to start.

## Matching guidance

- Match on meaning, not wording. "Expected salary", "compensation expectations", and "desired pay range" are one entry.
- Check the **Variants** line before declaring a question new — most "new" questions are rephrasings.
- Watch inversions ("do you require sponsorship" vs "are you authorized") and scope shifts (base salary vs total comp) — the Notes line exists to flag these.
- Company-specific questions ("why <company>?") match a pattern entry that stores the reusable skeleton; the tailored sentence per company is an ad-hoc answer, recorded in that application's `<id>.md`.
- If a canonical answer needs adaptation for this form (character limit, dropdown options), adapt it — and add a Notes line if the adaptation will recur.

## Rules

- **Answers containing user facts must trace to context docs** — `context/profile.md` or `context/career-diary.md`. Never fabricate eligibility, dates, skills, or numbers.
- **New user-supplied answers are accepted as-is and appended** — the user is the source of truth about themselves; never demand justification. If the answer contains a new durable fact, suggest also adding it to `context/profile.md`.
- Append new entries at apply time, immediately after the application is recorded — don't batch for later.
