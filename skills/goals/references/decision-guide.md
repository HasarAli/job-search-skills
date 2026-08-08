# Decision Guide — questions, trade-offs, recommendations

Each block is a decision, not a form field. Ask the question. If the user answers with a number or a name, write it down and move on. If they hesitate, hedge, or ask you what they should do, give them the trade-off in one sentence and the recommendation in the next — with the line from `career/profile.md` that grounds it. Then they choose; you record their choice, not yours.

Ground every recommendation. "Given eight years in payments and no infra roles on your timeline, I'd anchor on fintech backend" is advice; "fintech is a good market" is noise.

## Identity and market

- Which country or countries are you searching in?
- What industry or field? One primary, secondaries welcome.
- What language will you apply in — the same one you work in?
- Are you employed right now, and does the search need to stay confidential?

**Two countries at once.** Trade-off: a second country doubles the document set (different length, photo, and date conventions per the country table) and dilutes attention. Recommend one primary country and treat the second as a stretch, unless the profile shows work authorization in both.

**Industry switch.** Trade-off: the profile's strongest evidence is in the industry it was earned in; a switch spends that evidence. Recommend keeping the current industry as primary and the target industry as a secondary until the highlights carry transferable, measured work.

**Confidential search.** A yes changes what `optimize-linkedin` may turn on (no public "open to work"), and applications avoid the current employer's ATS. Record it here so those skills see it.

## Role targets and seniority

- Which titles are you targeting, ranked?
- For each: the one line that says why you fit it?
- What seniority are you aiming at, and would you take one level down for the right situation?
- Which titles, patterns, or work styles should we skip even when they match on paper?
- Any stretch role to keep on the radar?

**How many targets.** Trade-off: each target needs its own positioning and its own resume variant; more than three splits the search into searches. Recommend two, three at most, ranked.

**Seniority band.** Trade-off: aiming one level up buys upside on the offers that land and costs response rate on the ones that don't; aiming one level down buys volume and speed at a comp ceiling. Recommend the band the profile's scope actually evidences — team size led, blast radius of the systems owned, years at the current level — and name the specific evidence gap where the user wants a level the profile does not yet support.

**One level down.** A yes widens the search materially. Recommend yes when the user is unemployed, switching industry, or switching country; recommend no when they are employed and searching on their own timeline.

**Stretch role.** Cheap to keep — it costs one line in the file and a handful of postings a week. Recommend keeping one.

**Do not pursue.** Push for specifics: a title pattern, a work style, a company type. "Nothing boring" is not a filter; "no on-call rotations" and "no agency or consultancy work" are.

## Comp

- Walk-away floor and target, in total comp?
- Which currency and cadence does your market quote in — annual, monthly, hourly, day rate?
- Non-salary must-haves: equity, pension, healthcare, bonus, leave?

**Floor vs target.** Trade-off: a floor set at the current salary guarantees a lateral move; set too high it empties the shortlist. Recommend the floor at the number below which the user would rather stay put, and the target at the top of the band their level commands in that market — then say plainly which postings each number excludes.

**Equity.** Trade-off: private-company equity is illiquid and usually worth zero. Recommend counting it only where there is a real path to cash — a public company's RSUs, or a late-stage private with an established secondary market — and weighting base and cash bonus everywhere else.

**Cadence.** Take the market's convention from the country row, not the user's habit: a market that quotes monthly gross wants a monthly figure in the file, so `search` and `apply` compare like with like.

## Location and company

- Remote, hybrid, or on-site — what's acceptable, and what's preferred?
- How far will you commute, and from where?
- Would you relocate? Where, and on what terms?
- Company size and stage — startup, scaleup, enterprise, public sector, nonprofit?
- Anything about culture or working model that's a hard filter?

**Remote-only.** Trade-off: it is the single most restrictive filter in the search, and it caps comp in markets that localize pay. Recommend remote-only when the profile shows remote work already delivered; otherwise recommend remote-preferred with a named hybrid exception, and record the exception as a rule a search run can apply ("hybrid acceptable within 45 minutes of home").

**Company stage.** Trade-off: early stage pays in equity and scope, late stage in cash and stability. Recommend the stage matching what the profile is short of — scope, or evidence of operating at scale.

**Company size.** A floor on engineering-team size (or the equivalent function's size) is the practical version of "not the first hire". Recommend one when the user says they want an established team.

**Hard culture filters.** Turn each into something checkable in a posting: on-call, shift work, mandated office days, travel-heavy, agency model.

## Logistics and authorization

- Earliest start date and notice period?
- Travel tolerance — percentage or days per month?
- Hours constraints — part-time, caregiving windows, time zones you must overlap?
- Work authorization in each target country: already authorized, or sponsorship needed?

**Sponsorship.** Trade-off: needing it removes most of a country's postings, so it is worth knowing before the first search rather than after the twentieth rejection. Record the status per target country, and where sponsorship is needed, recommend biasing the search toward employers known to sponsor.

**Time zones.** For a remote search across countries, an overlap window is a filter — record the hours, not "flexible".

## Cadences

- Follow up after how many days of silence? Default 14.
- Retro after how many applications? Default 50.

Both defaults are fine for most searches. Recommend a shorter follow-up (7) for a market the user describes as fast-moving, and a smaller retro interval (25) when the user is applying at low volume and wants to correct sooner. Write them as `follow-up-days` and `retro-every` — `track` and `retro` read those names.
