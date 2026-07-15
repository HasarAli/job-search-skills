# RenderCV YAML skeleton

Copy this per region file (`resumes/<Name>-<role-slug>-<region>-<timestamp>.yaml`), replace every `<...>` placeholder, and delete sections the target region omits (see "Per-region sections" below). Field syntax and gotchas: [rendercv-guide.md](rendercv-guide.md).

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/rendercv/rendercv/refs/tags/v2.8/schema.json
cv:
  name: <Full Name>
  headline: <Target Role> · <Specialty>        # mirror role-preferences.md positioning
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
        highlights:                            # the user's chosen bullets, in highlights.md order
          - <Bullet 1 — XYZ format, see bullet-writing.md>
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
  theme: <classic|harvard|engineeringresumes|engineeringclassic|sb2nov|moderncv>
  page:
    size: <us-letter|a4>                       # per region convention
  # Spacing/font overrides only if the render overflows or the theme needs tuning;
  # theme defaults are fine to start. Field reference: rendercv-guide.md.
```

## Per-region sections — include or omit

Authoritative lookup: the onboard skill's `references/country-conventions.md`, keyed by the regions in `search/search-config.md`. It decides, per region:

- **Photo** — customary in some markets, actively discouraged (bias-screening) in others. `# photo:` stays commented unless conventions say include.
- **Personal details** — date of birth, nationality, marital status: some CV cultures expect them; most anglophone markets omit them entirely. Add as `custom_connections` entries only when required.
- **Paper size** — `us-letter` vs `a4` (`design.page.size`).
- **Length** — 1-page resume vs multi-page CV; drives how many optional sections survive.
- **Work authorization** — phrasing and whether to state it in the header; usually the ONLY content difference between two region files for the same role.
- **Date format and language** — set `locale.language` when the working language isn't English.

When two regions share all conventions, the files may be identical except the work-authorization `custom_connections` line — that's expected, not a bug.
