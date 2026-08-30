# Autofill Service Setup

An autofill service pre-fills application forms from a stored profile. Simplify is the documented adapter; any comparable service records the same config.

## Simplify walkthrough

1. **Extension and account.** The user installs the Simplify Copilot extension (simplify.jobs) in the browser they apply from and signs in there. Account creation, sign-in, and the resume upload are the user's own clicks.
2. **Profile fields.** Walk the fields — name, contact, location, work authorization, education, work history, links, demographics/EEO — sourcing answers from `candidate/profile.md` and `.agents/config/qa-bank.md`, one question to the user per gap. A complete profile is what makes the autofill deterministic.
3. **One uploaded resume at a time.** The service attaches the single resume it has stored. Pick the relevant base under `search/resumes/<role-slug>/<region>/` during setup. Before each submission, `apply` must ensure the service's stored file matches the application-local PDF.
4. **Config.** Write `.agents/config/autofill-config.json`:

```json
{
  "service": "Simplify | none",
  "resume_file": "<full filename of the uploaded resume>",
  "uploaded": "YYYY-MM-DD",
  "notes": "<anything service-specific>"
}
```

## Staleness

`resume_file` plus `uploaded` make a stale upload visible. During an application, `resume_file` must point at `search/applications/<stem>/<First>_<Last>_<Posted_Role>_Resume.pdf`; if it does not, prompt the user to replace the service's file, then update `resume_file` and `uploaded` in the same pass.
