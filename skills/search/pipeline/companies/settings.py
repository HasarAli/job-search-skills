"""The ``company_check:`` block of ``config.yaml``.

``null`` or absent turns the check off. When present, ``home`` and
``home_terms`` are required; every other key has a default. Validation returns
``(key_path, expected, found)`` triples so ``config.py`` can shape them like
its own structural errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Employer-of-record services and the phrase itself. Brand names that are also
#: common words ("Remote", "Oyster", "Multiplier") appear only in forms that
#: cannot be mistaken for ordinary prose.
DEFAULT_EOR_TERMS = (
    "employer of record", "eor", "deel", "remote.com", "oyster hr", "oysterhr",
    "velocity global", "globalization partners", "papaya global", "rippling eor",
)


@dataclass
class CheckSettings:
    home: str                                   # country the user lives and works in
    home_terms: list[str]                       # location words that mean home
    home_codes: list[str] = field(default_factory=list)     # ISO codes boards may give
    pay_terms: list[str] = field(default_factory=list)      # home currency marks: CAD, CA$
    region_terms: list[str] = field(default_factory=list)   # regions that include home
    away_terms: list[str] = field(default_factory=list)     # phrases limiting a role elsewhere
    eor_terms: list[str] = field(default_factory=lambda: list(DEFAULT_EOR_TERMS))
    linkedin_geo_id: int | None = None          # People-tab filter (browser mode)
    manage_tenants: bool = False                # add/remove board tenants by label
    people_check_cap: int = 10                  # People-tab checks per browser run


_LIST_KEYS = ("home_terms", "home_codes", "pay_terms", "region_terms", "away_terms", "eor_terms")
_KEYS = {"home", "linkedin_geo_id", "manage_tenants", "people_check_cap", *_LIST_KEYS}


def parse(raw: Any) -> tuple[CheckSettings | None, list[tuple[str, str, Any]]]:
    """Validate the block; ``(None, [])`` when the check is off."""
    if raw is None:
        return None, []
    if not isinstance(raw, dict):
        return None, [("company_check", "mapping or null", raw)]

    errors: list[tuple[str, str, Any]] = []
    for key in sorted(set(raw) - _KEYS):
        errors.append((f"company_check.{key}", f"known key (allowed: {', '.join(sorted(_KEYS))})", key))

    home = raw.get("home")
    if not isinstance(home, str) or not home.strip():
        errors.append(("company_check.home", "non-empty string", home))

    lists: dict[str, list[str]] = {}
    for key in _LIST_KEYS:
        value = raw.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            errors.append((f"company_check.{key}", "list of non-empty strings", value))
            continue
        lists[key] = [v.strip() for v in value]
    if not lists.get("home_terms"):
        if "company_check.home_terms" not in {e[0] for e in errors}:
            errors.append(("company_check.home_terms", "non-empty list of strings", raw.get("home_terms")))

    geo = raw.get("linkedin_geo_id")
    if geo is not None and (isinstance(geo, bool) or not isinstance(geo, int)):
        errors.append(("company_check.linkedin_geo_id", "integer or null", geo))
    manage = raw.get("manage_tenants", False)
    if not isinstance(manage, bool):
        errors.append(("company_check.manage_tenants", "true or false", manage))
    cap = raw.get("people_check_cap", 10)
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
        errors.append(("company_check.people_check_cap", "integer >= 0", cap))

    if errors:
        return None, errors
    settings = CheckSettings(
        home=home.strip(),
        home_terms=lists["home_terms"],
        linkedin_geo_id=geo,
        manage_tenants=manage,
        people_check_cap=cap,
    )
    for key in _LIST_KEYS[1:]:
        if key in lists:
            setattr(settings, key, lists[key])
    return settings, []
