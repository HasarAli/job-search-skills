# Q&A Bank Format

`.agents/config/qa-bank.md` is the answer store for application-form questions — work authorization, salary expectations, notice period, relocation, start date, "why us" skeletons. It compounds: every application appends what it learned, so each successive form has fewer gaps.

## Structure

One entry per question pattern:

```markdown
## <Question pattern>

**Answer:** <canonical answer, as it should be typed into a form>

**Variants:** <other phrasings that mean the same question>
**Notes:** <when to deviate — per-country, per-role, per-seniority>
```

Example:

```markdown
## Are you legally authorized to work in <country>?

**Answer:** Yes

**Variants:** "Do you have the right to work in…", "Work authorization status",
"Will you now or in the future require sponsorship?" (inverse — answer No)
**Notes:** Sponsorship questions are the inverted form; read carefully before reusing.
```

Top-level headers (`# Eligibility`, `# Compensation`, `# Motivation`) group a bank that has grown; flat is fine to start.

## Matching

- Match on meaning: "expected salary", "compensation expectations", and "desired pay range" are one entry.
- Read the **Variants** line before treating a question as new — most new-looking questions are rephrasings.
- Inversions ("do you require sponsorship" vs "are you authorized") and scope shifts (base vs total comp) flip the answer; the Notes line is where they get flagged.
- "Why <company>?" matches the pattern entry holding the reusable skeleton; the tailored sentence is written for that application alone and is not banked.
- A canonical answer that needs adapting to this form (character limit, dropdown options) gets adapted, plus a Notes line when the adaptation will recur.

## Rules

- Answers carrying facts about the user trace to `career/profile.md` or `career/career-diary.md`.
- An answer the user supplies is appended as given — the user is the source of truth about themselves. When it carries a durable new fact, suggest adding it to `career/profile.md` and leave the call to them.
