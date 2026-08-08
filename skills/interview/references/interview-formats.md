# Interview Formats

One section per format: what it tests, the question set to prep, the method the user answers with, and the bar you grade a rehearsed answer against. Prep only the format that was scheduled — a system design pack does nothing for a recruiter screen.

Methods are named and standard. STAR, a stated design framework, and think-aloud are what interviewers already expect; invented methodology costs the user the round.

## STAR — the behavioural method

**S**ituation (one line of context) → **T**ask (what the user owned) → **A**ction (what *they* did, first person, the bulk of the answer) → **R**esult (the outcome, with a number where `career/profile.md` has one).

Two minutes spoken. "We" in the Action section is the most common failure: it hides which part was theirs.

## Recruiter screen

**Tests:** fit against the JD's hard filters, comp alignment, notice period, and whether the user can describe their work to a non-engineer.

**Question set:**
- Walk me through your background / tell me about yourself.
- Why are you looking, and why this company?
- What are you working on right now, and what is your part in it?
- Comp expectations, notice period, location and remote setup, work authorization.
- Anything on the resume that reads as a jump, a gap, or a title mismatch.

**Method:** a 90-second narrative — current role, the through-line of the last two moves, why this role is the next one. Comp answers come from `goals/search-filters.md`, stated as a band with the floor at the bottom.

**Bar:** no jargon a recruiter cannot repeat to the hiring manager; the comp number stated without hedging; a reason for leaving that is about what they are going toward.

## Hiring-manager

**Tests:** scope and ownership at the claimed level, judgment, and whether the user's wants match the team's work.

**Question set:**
- The hardest technical problem you have owned end to end.
- A disagreement with an engineer, a manager, or a PM, and how it resolved.
- Something you shipped that failed, and what changed afterwards.
- How you decide what to build first when the plan is not settled.
- Mentoring, code review, and how you raise the level around you.
- Why this team specifically.

**Method:** STAR, with the Action section carrying the technical judgment — the option not taken and why.

**Bar:** the story is scoped to the level the role hires at; the result has a number or an explicit "no number, here is the observable change"; the user names a trade-off rather than only a solution.

## Technical / coding

**Tests:** problem decomposition under time pressure, the language they claim, and whether they communicate while working.

**Question set:** data structures and algorithms at the JD's stated level, one or two questions in 45 minutes, plus follow-ups on complexity and edge cases. Live debugging or a small feature in the team's stack where the JD names one.

**Method — think-aloud:** restate the problem → ask clarifying questions → work one concrete example by hand → state the brute force with its complexity → optimize and say what the optimization buys → write the code, narrating → test it on the example and on the edges.

**Bar:** the clarifying questions come before any code; complexity is stated unprompted; the user notices their own bug before the interviewer does; silence never runs past ten seconds.

## System design

**Tests:** whether the user can hold a whole system, size it, and defend the trade-offs — the growth area named in `goals/role-preferences.md`.

**Question set:** design a well-known product surface (feed, chat, upload and serve media, rate limiter, notification fan-out), then a deep dive the interviewer picks. Frontend-leaning loops ask for component architecture, state ownership, caching, and rendering strategy on the same footing.

**Method — the four-step framework** (Alex Xu's, and what most loops run):
1. **Scope** — functional requirements, non-functional requirements, and the numbers: users, requests per second, read/write ratio, storage.
2. **High-level design** — boxes, arrows, and the API between them; the data model.
3. **Deep dive** — the component the interviewer names, taken to storage, indexing, caching, and failure.
4. **Wrap up** — bottlenecks, what breaks at 10×, what was traded away.

**Bar:** requirements are pinned before any box is drawn; every estimate is a stated number the user did out loud; at least one decision is defended against its named alternative; the design is not gold-plated past the stated requirements.

## Panel / onsite

**Tests:** consistency across interviewers, and endurance. Counts as one round.

**Prep:** one slot per interviewer, each mapped to a format above from the schedule and the interviewers' public profiles. Repeated stories are expected across slots — the panel compares notes on consistency, not novelty.

**Bar:** the same story told twice keeps the same facts and the same numbers; energy in the last slot matches the first.

## Take-home

**Tests:** production judgment without supervision — structure, tests, README, and the discipline to stop.

**Prep:**
- Time-box to the stated budget and say in the README where the box cut something off.
- README first: how to run it, the design decisions, what was left out and why.
- Tests on the logic that matters, not coverage theatre.
- Commit history that reads as steps.
- Expect a follow-up call on it: prep to defend every decision and to name the first thing they would change.

**Bar:** it runs from a clean clone on the stated commands; scope matches the brief; the README answers "why" and not only "how".

## Final / executive

**Tests:** closing signals — motivation, level of interest, comp reality, and how the user handles an unstructured conversation.

**Question set:**
- What do you want your next two years to look like?
- What would make you turn this down?
- Comp, competing processes, and start date.
- Their questions for the company, which carry real weight in this round.

**Method:** direct answers, no rehearsed narrative. Comp comes from `goals/search-filters.md`, competing processes stated as a timeline rather than a name.

**Bar:** the user states a floor without apologizing for it, and asks at least one question that only someone who wants the job would ask.
