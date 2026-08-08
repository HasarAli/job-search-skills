#!/usr/bin/env python3
"""Shared helpers for the board adapters (ATS + remote).

Registries and scope are DATA, not code: the ATS targets, the remote feeds, the
discipline token lists and the geo allowlists all live in one JSON file
(`.agents/config/sources.json`), passed in per run via --config. These adapters
are generic engines — point them at a different config to search any profession
or region. See the `sources` skill.
"""
import json
from datetime import datetime
from pathlib import Path


def load_config(path):
    """Return the parsed sources.json config."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def filters(config):
    """Return (discipline, geo) dicts from the config's `filters` key."""
    f = config.get("filters", {})
    return f.get("discipline", {}), f.get("geo", {})


def live_rows(config, key):
    """Return the registry rows under `key` whose status is `live`."""
    return [r for r in config.get(key, []) if (r.get("status") or "").lower() == "live"]


def discipline_ok(text, disc):
    """Keep text matching an include token and no exclude token. Empty include => keep all."""
    t = text.lower()
    if any(x in t for x in disc.get("exclude", [])):
        return False
    inc = disc.get("include", [])
    return True if not inc else any(x in t for x in inc)


def iso_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except (ValueError, AttributeError):
        return None


def is_us_ca(loc, geo):
    """Geo gate for ATS postings: keep US/CA worksites (country hint, city, state/province, remote)."""
    if not loc:
        return False
    t = loc.lower()
    if any(c in t for c in geo.get("country_hints", [])):
        return True
    cities = set(geo.get("us_cities", [])) | set(geo.get("ca_cities", []))
    if any(city in t for city in cities):
        return True
    codes = set(geo.get("us_states", [])) | set(geo.get("ca_provinces", []))
    tokens = {tok.strip(" ,.").upper() for tok in loc.replace("/", " ").split()}
    if tokens & codes:
        return True
    if "remote" in t and not any(x in t for x in geo.get("remote_exclude_hint", [])):
        return True
    return False


def remote_geo_ok(loc, geo):
    """Remote-first gate: keep unless the role is explicitly pinned outside North America."""
    if not loc:
        return True
    t = loc.lower()
    if any(h in t for h in geo.get("na_hint", [])):
        return True
    non_na = geo.get("non_na", [])
    if any(w in t for w in ("anywhere", "worldwide", "global", "remote")):
        return not any(n in t for n in non_na)  # 'remote' alone ok; 'remote - europe' not
    if any(n in t for n in non_na):
        return False
    return True  # unknown/blank -> keep (remote boards default to open)
