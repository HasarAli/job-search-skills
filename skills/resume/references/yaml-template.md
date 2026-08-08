# RenderCV YAML skeleton

> A **seed**: copied once into `.agents/templates/resume.yaml`, which is where every later customization lives. A skill update overwrites this file.

Copy this into `.agents/templates/resume.yaml`, replace every `<...>` placeholder, and drop the sections the target regions omit (see "Per-region sections" below). Field syntax and gotchas: [rendercv-guide.md](rendercv-guide.md).

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/rendercv/rendercv/refs/tags/v2.8/schema.json
cv:
  name: <Full Name>
  headline: <Target Role> · <Specialty>        # mirror goals/role-preferences.md positioning
  location: <City, Region>                     # granularity per region convention
  email: <email>
  phone: "<+E.164 number>"                     # quoted, E.164 only; omit if region omits phone
  # photo: <path/to/photo.jpg>                 # ONLY where the region expects one
  social_networks:
    - network: LinkedIn                        # or GitHub, GitLab, ORCID, ...
      username: <username>
  custom_connections:                          # free-form header lines, e.g. work authorization
    - fontawesome_icon: globe
      placeholder: <work-authorization line for this region>
      url:

  sections:                                    # dict: section title -> entry list
    Summary:                                   # TextEntry — plain strings
      - <1–2 sentence positioning statement for the target role.>

    Experience:                                # ExperienceEntry
      - company: <Company>
        position: <Title>
        location: <City or Remote>
        start_date: <YYYY-MM>
        end_date: present                      # or <YYYY-MM>
        highlights:                            # the user's chosen bullets, in career/highlights.md order
          - <Bullet 1 — XYZ format>
          - <Bullet 2>
      - company: <Earlier Company>
        position: <Title>
        location: <City>
        start_date: <YYYY-MM>
        end_date: <YYYY-MM>
        highlights:
          - <Bullet>

    Skills:                                    # OneLineEntry — order groups by target-role relevance
      - label: <Group, e.g. Core tools>
        details: <comma, separated, items>
      - label: <Group 2>
        details: <items>

    Education:                                 # EducationEntry
      - institution: <Institution>
        area: <Field of study>
        degree: <B.S. / M.A. / ...>
        date: <YYYY>                           # free-form; or start_date/end_date

    # Optional sections — include only when relevant AND regionally expected:
    # Projects:            # NormalEntry: name + summary/highlights
    # Certifications:      # OneLineEntry or NormalEntry
    # Publications:        # PublicationEntry: title, authors, date
    # Languages:           # OneLineEntry — expected in most non-anglophone markets

design:
  theme: <classic|harvard|engineeringresumes|engineeringclassic|sb2nov|moderncv>  # pick per industry/region — themes.md
  page:
    size: <us-letter|a4>                       # Letter for US/Canada, A4 nearly everywhere else — country-conventions.md
    top_margin: <e.g. 0.7in or 6mm>             # tighten only if the render overflows one page
    bottom_margin: <...>
    left_margin: <...>
    right_margin: <...>
  typography:
    font_size:
      body: <e.g. 10-10.5pt>                    # theme default is fine to start
  section_titles:
    space_above: <e.g. 0.5cm>                   # tighten with sections.space_between_* to fit one page
  sections:
    space_between_regular_entries: <e.g. 1.2em>
  # Full field reference, all 6 theme defaults, and a worked tightened-spacing
  # example: references/themes.md. Only override fields you're actually changing —
  # theme defaults apply to everything else.
```

## Per-region sections — include or omit

Authoritative lookup: `.agents/config/conventions/country-conventions.md`, keyed by the regions in `goals/search-filters.md`. It decides, per region:

- **Photo** — customary in some markets, actively discouraged (bias-screening) in others. `# photo:` stays commented unless conventions say include.
- **Personal details** — date of birth, nationality, marital status: some CV cultures expect them; most anglophone markets omit them entirely. Add as `custom_connections` entries only when required.
- **Paper size** — `us-letter` vs `a4` (`design.page.size`).
- **Length** — 1-page resume vs multi-page CV; drives how many optional sections survive.
- **Work authorization** — phrasing and whether to state it in the header; usually the ONLY content difference between two region files for the same role.
- **Date format and language** — set `locale.language` when the working language isn't English.

Two regions sharing every convention produce files that differ only in the work-authorization `custom_connections` line. That is the expected outcome.
