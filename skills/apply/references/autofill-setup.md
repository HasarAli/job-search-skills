# Autofill Service Setup

An autofill service pre-fills application forms from a stored profile, cutting per-application time sharply. Setup is optional — the apply skill works without one (fields are filled manually from `qa-bank.md`). Simplify is the default adapter documented below; any comparable service is fine, and the same config contract applies.

## Simplify walkthrough

1. **Install the extension.** Have the user install the Simplify Copilot browser extension (simplify.jobs) in the browser they apply from, and create/log into their Simplify account. Account creation and login are user actions — never enter credentials for them.
2. **Complete the profile.** Walk the user through Simplify's profile fields (name, contact, location, work authorization, education, work history, links, demographics/EEO where applicable). Source answers from `context/profile.md` and `applications/qa-bank.md`; ask the user for anything missing, one question at a time. The more complete the profile, the more deterministic the autofill.
3. **Upload exactly ONE canonical resume.** Simplify's free tier stores one resume, and that stored file is what gets attached/parsed on autofill. Pick the user's current canonical resume PDF from `resumes/` — full filename matters (`<Name>-<role-slug>-<region>-<timestamp>.pdf`). The user performs the upload.
4. **Record the config.** Write `applications/autofill-config.md`:

```markdown
# Autofill Config

- service: Simplify
- resume_file: <full filename of the uploaded resume>
- uploaded: YYYY-MM-DD
- notes: <anything service-specific>
```

## Staleness

The full filename + upload date make staleness detectable: if `resumes/` contains a newer render than `resume_file`, the service is serving an outdated resume. **A re-rendered resume means re-upload + config update** — prompt the user to replace the file in the service, then update `resume_file` and `uploaded`.

Before each apply batch, compare `resume_file` against the newest matching resume in `resumes/` and flag a mismatch.

## Other services / no service

- Another service: same steps conceptually — install/configure, one canonical resume, record `service`, `resume_file`, `uploaded` in `autofill-config.md`.
- No service: write `autofill-config.md` with `service: none` so the first-run branch doesn't re-trigger; every field is filled from `qa-bank.md` and user answers.
