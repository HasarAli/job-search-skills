# Job Search Skills

A job search you run by talking to an AI coding agent. You supply the raw material and the
decisions; it keeps your documents, your search, and your tracker in step with them.

Fourteen skills cover the whole thing — turning your old resumes and reviews into a record
of your background, deciding what you are looking for, writing and rendering your resume,
tuning your LinkedIn, finding jobs every day, filling in the applications, reading
recruiter mail, tracking every outcome, and prepping each interview.

Nothing here is tied to one agent. The instructions live in plain files that any of them
can read.

## Install

```
npx skills add https://github.com/HasarAli/job-search-skills
```

Then open the folder you want your job search to live in and say **"set up my job
search"**. The `init` skill builds the whole thing from scratch — folders, starter
documents, a README written for you, and the first commit. There is no template to clone
and nothing to fill in by hand.

From there, say **"process my drop folder"** and follow what each skill tells you next.

You will need Python for the job-search and resume tooling; the skills walk you through
installing what they use, when they first need it.

## Skills

Each of these is a job the agent knows how to do. **Bold** ones happen only when you ask
for them by name; the rest happen on their own when the moment calls for it.

| Name | What it does |
|---|---|
| **init** | sets the project up from scratch |
| intake | turns your dropped documents into a record of your background |
| **goals** | walks you through what you are looking for |
| highlights | turns your achievements into resume-ready lines |
| resume | builds and renders your resume |
| **optimize-linkedin** | audits and rewrites your LinkedIn profile |
| **sources** | decides which boards and inboxes get searched |
| search | produces the daily shortlist |
| apply | fills in and submits applications |
| inbox | reads and sorts recruiter messages |
| track | keeps applications.csv current |
| **retro** | finds where your applications are getting stuck |
| interview | prepares you for a specific interview, and debriefs it after |
| **teach** | teaches you a topic across multiple sessions |

Nothing is ever sent on your behalf without your explicit yes — every application, every
reply, every edit to your live profile is shown to you first.

## Your data stays yours

No personal data ships with these skills. Everything about you — your background, your
targets, your resumes, your applications — lives in your own repo on your own machine,
created by `init` and committed as you go, so nothing is ever really lost.

## Design

How the skills are put together, what each one owns, and the rules for editing them:
[DESIGN.md](DESIGN.md).

## Licence

`skills/teach/` is vendored from [mattpocock/skills](https://github.com/mattpocock/skills)
under the MIT licence, with one repo-local modification — see `skills/teach/LICENSE`.
