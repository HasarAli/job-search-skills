# Autofill Service Setup

An autofill service pre-fills application forms from a stored profile. Simplify is the documented adapter; any comparable service records the same config.

## Simplify walkthrough

1. **Extension and account.** The user installs the Simplify Copilot extension (simplify.jobs) in the browser they apply from and signs in there. Account creation, sign-in, and the resume upload are the user's own clicks.
2. **Profile fields.** Walk the fields — name, contact, location, work authorization, education, work history, links, demographics/EEO — sourcing answers from `career/profile.md` and `.agents/config/qa-bank.md`, one question to the user per gap. A complete profile is what makes the autofill deterministic.
3. **One canonical resume.** The service attaches the single resume it has stored, so pick the user's current render from `resumes/<YYYY-MM-DD>/` and have them upload that file.
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

`resume_file` plus `uploaded` are what make a stale upload visible: a newer render under `resumes/<YYYY-MM-DD>/` means the service still serves the old PDF. Prompt the user to replace the file in the service, then update `resume_file` and `uploaded` in the same pass.
