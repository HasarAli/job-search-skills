"""Config loading and structural validation.

All search state resolves against the project-local directory ``.agents/search/``
(overridable via ``SEARCH_STATE_DIR`` — the tests point it at a temp dir). On
first run the shipped ``defaults/`` (next to this package) are copied into that
directory, then the (now user-owned) ``config.yaml`` is read and validated.

Structural problems refuse the run *before any network call*. ``load_config``
collects every error it can find and raises :class:`ConfigError`, which carries
a list of dicts shaped ``{"path", "expected", "found"}``. ``path`` is the key
path (e.g. ``sources[2].tenants``) rooted at the file it points into — the
config file path for config errors, the filters file path for filters errors.
The caller prints these as JSON to stderr and exits 2.

Only the standard library plus ``pyyaml`` (declared in pyproject.toml) are used
here.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from .model import Posting, Query

# ---- state directory -------------------------------------------------------

SEARCH_STATE_ENV = "SEARCH_STATE_DIR"
DEFAULT_STATE_DIR = Path(__file__).resolve().parents[3] / "search"

# Adapter keys that may appear as ``sources[].name`` (the seven v1 adapters).
KNOWN_SOURCES = (
    "jobspy",
    "wwr",
    "greenhouse",
    "ashby",
    "lever",
    "workday",
    "agent-json",
)

# Keys each source block is allowed to carry, keyed by adapter name.
SOURCE_KEYS: dict[str, set[str]] = {
    "jobspy": {"name", "site_names", "search_term"},
    "wwr": {"name"},
    "greenhouse": {"name", "tenants"},
    "ashby": {"name", "tenants"},
    "lever": {"name", "tenants"},
    "workday": {"name", "tenants"},
    "agent-json": {"name", "path"},
}

DEFAULT_LEVELS_ATTRIBUTION = "https://www.levels.fyi"


class ConfigError(Exception):
    """Structural config problem(s).

    ``errors`` is a list of JSON-serialisable dicts, one per problem, each
    shaped ``{"path": ..., "expected": ..., "found": ...}``.
    """

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} structural config error(s)")


@dataclass
class Config:
    query: Query
    sources: list[dict[str, Any]]
    filters: list[str]
    post_enrichment_filters: list[str]
    comp_floor: float | None
    seen_db_path: Path
    visa_wages_dir: Path
    levels_attribution: str


# ---- path helpers ----------------------------------------------------------


def state_dir() -> Path:
    """The project-local search state dir (``.agents/search/``), overridable
    via ``SEARCH_STATE_DIR`` (the tests point it at a temp dir)."""
    return Path(os.environ.get(SEARCH_STATE_ENV, str(DEFAULT_STATE_DIR))).expanduser()


def _defaults_dir() -> Path:
    """Location of the shipped defaults (``defaults/`` next to this package)."""
    repo = Path(__file__).resolve().parent.parent / "defaults"  # search/defaults
    if (repo / "config.yaml").exists():
        return repo
    # Installed wheel: defaults shipped as data-files next to the interpreter.
    for candidate in (Path(sys.prefix) / "defaults", Path(sys.prefix) / "search" / "defaults"):
        if (candidate / "config.yaml").exists():
            return candidate
    return repo


def _bootstrap(home: Path) -> None:
    """First-run bootstrap: copy ``search/defaults/`` into the state dir when
    the dir or its ``config.yaml`` is missing, then proceed."""
    if home.is_dir() and (home / "config.yaml").is_file():
        return
    defaults = _defaults_dir()
    home.mkdir(parents=True, exist_ok=True)
    shutil.copytree(defaults, home, dirs_exist_ok=True)


# ---- error shaping ---------------------------------------------------------


def _found(value: Any) -> str:
    """Render an observed value for the ``found`` field of a structural error.

    Strings pass through bare (the outer ``json.dumps`` of the error dict adds
    the quotes); everything else is JSON-encoded so it stays readable.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(value)


def _err(root: str, key_path: str, expected: str, found: Any) -> dict[str, str]:
    """One structural error dict. ``path`` is the key path rooted at ``root``
    (the file the error points into — config path or filters path)."""
    return {
        "path": f"{root}:{key_path}" if key_path else root,
        "expected": expected,
        "found": _found(found),
    }


# ---- per-section parsers (collect every error, don't fail fast) ------------


def _parse_query(data: dict[str, Any], root: str, errors: list[dict[str, Any]]) -> Query:
    raw = data.get("query")
    if not isinstance(raw, dict):
        errors.append(_err(root, "query.roles", "non-empty list of strings", None))
        errors.append(_err(root, "query.region", "non-empty string", None))
        return Query(roles=[], region="")

    roles: list[str]
    raw_roles = raw.get("roles")
    if (
        isinstance(raw_roles, list)
        and raw_roles
        and all(isinstance(r, str) and r.strip() for r in raw_roles)
    ):
        roles = [r.strip() for r in raw_roles]
    else:
        roles = []
        errors.append(_err(root, "query.roles", "non-empty list of strings", raw_roles))

    raw_region = raw.get("region")
    if isinstance(raw_region, str) and raw_region.strip():
        region = raw_region.strip()
    else:
        region = ""
        errors.append(_err(root, "query.region", "non-empty string", raw_region))

    remote: bool | None
    raw_remote = raw.get("remote")
    if raw_remote is None:
        remote = None
    elif isinstance(raw_remote, bool):
        remote = raw_remote
    else:
        remote = None
        errors.append(_err(root, "query.remote", "true, false, or null", raw_remote))

    posted_since: datetime | None = None
    raw_psh = raw.get("posted_since_hours")
    if raw_psh is not None:
        if isinstance(raw_psh, bool) or not isinstance(raw_psh, (int, float)) or raw_psh <= 0:
            errors.append(_err(root, "query.posted_since_hours", "positive number or null", raw_psh))
        else:
            posted_since = datetime.now(timezone.utc) - timedelta(hours=float(raw_psh))

    return Query(roles=roles, region=region, remote=remote, posted_since=posted_since)


def _parse_sources(data: dict[str, Any], root: str, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw = data.get("sources")
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append(_err(root, "sources", "list of source blocks", raw))
        return []

    sources: list[dict[str, Any]] = []
    for i, block in enumerate(raw):
        base = f"sources[{i}]"
        if not isinstance(block, dict):
            errors.append(_err(root, base, "source block (mapping)", block))
            continue
        name = block.get("name")
        if name not in KNOWN_SOURCES:
            errors.append(_err(root, f"{base}.name", f"one of {', '.join(KNOWN_SOURCES)}", name))
            continue
        allowed = SOURCE_KEYS[name]
        for key in sorted(set(block) - allowed):
            errors.append(
                _err(root, f"{base}.{key}", f"known key for adapter {name!r} (allowed: {', '.join(sorted(allowed))})", key)
            )
        sources.append(block)
    return sources


def _parse_name_list(data: dict[str, Any], key: str, root: str, errors: list[dict[str, Any]]) -> list[str]:
    raw = data.get(key)
    if raw is None:
        return []
    if not isinstance(raw, list) or any(not isinstance(x, str) or not x.strip() for x in raw):
        errors.append(_err(root, key, "list of predicate names", raw))
        return []
    return [x.strip() for x in raw]


def _parse_optional_number(data: dict[str, Any], key: str, root: str, errors: list[dict[str, Any]]) -> float | None:
    raw = data.get(key)
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        errors.append(_err(root, key, "number or null", raw))
        return None
    return float(raw)


# ---- filters.py loading ----------------------------------------------------


def _load_filters_from(path: Path) -> dict[str, Callable[[Posting], bool]]:
    """Import a filters module by path (importlib) and return ``{name: fn}``.

    A predicate is ``fn(posting: Posting) -> bool`` (True = keep). Only
    callables *defined in* the module are collected (imports are skipped).
    Import failure is a structural error (:class:`ConfigError`).
    """
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ConfigError([_err(str(path), "", "importable Python module of predicates", "file not found")])

    # ``hash()`` is randomised per process, but the name only needs to be a
    # valid, unique identifier for the lifetime of this import.
    module_name = f"_job_search_filters_{abs(hash(str(path))) & 0x7FFFFFFF:x}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load filters module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 — any import failure is structural
        raise ConfigError(
            [_err(str(path), "", "importable Python module of predicates", f"{type(exc).__name__}: {exc}")]
        ) from exc

    predicates: dict[str, Callable[[Posting], bool]] = {}
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if callable(obj) and getattr(obj, "__module__", None) == module.__name__:
            predicates[name] = obj
    return predicates


def load_filters() -> dict[str, Callable[[Posting], bool]]:
    """Import the user-owned ``filters.py`` (in the search state dir) by path
    and return ``{name: predicate}``, where each predicate is
    ``fn(Posting) -> bool`` (True = keep). Import failure is a structural error."""
    return _load_filters_from(state_dir() / "filters.py")


# ---- entry points ----------------------------------------------------------


def load_config(config_path: str | Path | None = None) -> Config:
    """Load and structurally validate the config.

    ``config_path`` overrides the default ``$SEARCH_STATE_DIR/config.yaml``
    (the CLI ``--config`` flag). Raises :class:`ConfigError` with every
    structural problem collected; the caller prints them and exits 2.
    """
    home = state_dir()
    _bootstrap(home)

    resolved = (Path(config_path) if config_path else home / "config.yaml").expanduser().resolve()
    root = str(resolved)

    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError([_err(root, "", "readable config.yaml", str(exc))]) from exc

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError([_err(root, "", "valid YAML", str(exc))]) from exc

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError([_err(root, "", "mapping at the top level", _found(data))])

    errors: list[dict[str, Any]] = []
    query = _parse_query(data, root, errors)
    sources = _parse_sources(data, root, errors)
    filters = _parse_name_list(data, "filters", root, errors)
    post_filters = _parse_name_list(data, "post_enrichment_filters", root, errors)
    comp_floor = _parse_optional_number(data, "comp_floor", root, errors)

    # Every named filter must resolve to a predicate in the user's filters.py.
    defined: dict[str, Callable[[Posting], bool]] | None = None
    try:
        defined = _load_filters_from(home / "filters.py")
    except ConfigError as exc:
        errors.extend(exc.errors)
    if defined is not None:
        for key, names in (("filters", filters), ("post_enrichment_filters", post_filters)):
            for i, name in enumerate(names):
                if name not in defined:
                    errors.append(_err(root, f"{key}[{i}]", "predicate defined in filters.py", name))

    if errors:
        raise ConfigError(errors)

    return Config(
        query=query,
        sources=sources,
        filters=filters,
        post_enrichment_filters=post_filters,
        comp_floor=comp_floor,
        seen_db_path=home / "seen.db",
        visa_wages_dir=home / "visa-wages",
        levels_attribution=DEFAULT_LEVELS_ATTRIBUTION,
    )
