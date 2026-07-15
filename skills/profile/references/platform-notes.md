# Platform Notes

Platform-specific behavior for crawling, reviewing, and editing. **All platform-behavior
claims here are changeable** — platforms redesign UIs, rename settings, and retune
search without notice. Re-verify anything load-bearing against the live UI (or a quick
web search) before relying on it, and update this file when reality differs.

## LinkedIn (default)

### What recruiter search actually indexes

Recruiters use LinkedIn Recruiter, which searches structured fields. Weight review
effort accordingly:

- **Headline** — highest-visibility keyword field; appears in every search result row.
  Title + specialization keywords beat slogans.
- **Current/past job titles** — filterable fields; the title text on each experience
  entry matters independently of the headline.
- **Skills** — filterable; entries missing from the skills list can miss skill-filtered
  searches even if mentioned in prose. Top/pinned skills carry display weight.
- **About + experience descriptions** — keyword-indexed free text; naturally worded
  keywords help, keyword stuffing reads badly to the human who clicks through.
- **Location** — a hard filter in most searches; a vague or wrong location silently
  drops the profile from results.

### Open to Work

Settings > "Open to work" (also reachable from the profile top card):

- **Visibility choice**: "Recruiters only" (hidden from the user's current employer's
  recruiters, best-effort) vs "All LinkedIn members" (adds the green #OpenToWork photo
  frame). Which to choose is the user's call — surface the trade-off, don't decide.
- Configurable: target job titles, location types (on-site/hybrid/remote), locations,
  start-date urgency, employment types. These feed recruiter-side filters — treat them
  as seriously as the headline.

### Featured section

Manually curated showcase (posts, articles, links, documents) directly under About.
Order is user-controlled; first items get the visibility. Empty Featured is a common
easy win: pin best work, a portfolio link, or a strong post.

### Editing mechanics (for the apply step)

- Each section has its own pencil/edit affordance opening a modal; save per modal.
- Headline limit ~220 chars, About ~2,600 chars — verify current limits in the modal's
  counter rather than trusting these numbers.
- After saving, re-read the section to confirm the change persisted before moving on.
- Photo/cover upload dialogs are file pickers — this is one reason image changes are
  manual-only.

## Xing (DACH-region platform)

- Structure is broadly similar: headline ("Ich biete" / offering fields), work
  experience, skills ("Fähigkeiten und Kenntnisse"), and a wants/offers pair
  ("Ich suche" / "Ich biete") that recruiters filter on — treat those two lists like
  LinkedIn's skills + open-to-work targets combined.
- Job-seeking status has its own visibility toggle for recruiters.
- Profile language matters: recruiters there commonly search in the local working
  language; align profile language with `search-config.md`'s working language.
- UI labels differ by account language; navigate by section semantics, not label text.

## Other platforms (generic fallback)

When `search-config.md` names a platform not covered above:

1. Crawl by section semantics from `crawl-guide.md` — headline-equivalent, summary,
   experience, skills, visibility/job-seeking settings — mapping to whatever the
   platform calls them; record the platform's own names in the snapshot.
2. Before reviewing, spend one quick web search on "how do recruiters search on
   <platform>" to learn which fields are filterable; give those fields the LinkedIn-
   headline level of attention.
3. Same editing rules: one confirmed edit at a time, verify saves, images manual-only.
4. Append what was learned about the platform to this file for next time.
