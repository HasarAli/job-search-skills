"""Built-in filter predicates (cheap filters + post-enrichment floor).

All built-ins pass on unknown/missing data (``True`` = keep). Their names are
the ``filtered:<name>`` reasons recorded in the ledger.

Each built-in is callable as ``fn(posting, arg)`` (``arg`` only for
``freshness``/``region``/``comp_floor``) and exposes:

* ``.name`` — the canonical reason name (``freshness``, ``region``, ``remote``,
  ``comp_floor``);
* ``.describe(posting) -> str | None`` — the observed value for the ledger's
  ``reason`` column (the value the predicate judged on); ``None`` when nothing
  meaningful was observed.

Semantics:

* ``freshness(posting, since)`` — keep if ``posted_at >= since`` or
  ``posted_at is None``.
* ``region(posting, region)`` — keep if ``region`` matches ``location``
  case-insensitively (substring) or ``location is None``.
* ``remote(posting)`` — keep if ``remote is not False`` (``None`` passes).
* ``comp_floor(posting, floor)`` — keep if ``posting.comp`` is ``None``, or
  ``posting.comp.floor_value`` is ``None``, or ``floor_value >= floor``.
"""

from __future__ import annotations

from datetime import datetime

from pipeline.model import Posting


class _Builtin:
    """Base for the built-ins: carries the canonical ``name``."""

    name: str = ""

    def describe(self, posting: Posting) -> str | None:
        return None


class _Freshness(_Builtin):
    name = "freshness"

    def __call__(self, posting: Posting, since: datetime) -> bool:
        return posting.posted_at is None or posting.posted_at >= since

    def describe(self, posting: Posting) -> str | None:
        if posting.posted_at is None:
            return None
        return posting.posted_at.isoformat()


class _Region(_Builtin):
    name = "region"

    def __call__(self, posting: Posting, region: str) -> bool:
        if posting.location is None:
            return True
        return region.casefold() in posting.location.casefold()

    def describe(self, posting: Posting) -> str | None:
        return posting.location


class _Remote(_Builtin):
    name = "remote"

    def __call__(self, posting: Posting) -> bool:
        return posting.remote is not False

    def describe(self, posting: Posting) -> str | None:
        if posting.remote is None:
            return None
        return "true" if posting.remote else "false"


class _CompFloor(_Builtin):
    name = "comp_floor"

    def __call__(self, posting: Posting, floor: float) -> bool:
        if posting.comp is None:
            return True
        if posting.comp.floor_value is None:
            return True
        return posting.comp.floor_value >= floor

    def describe(self, posting: Posting) -> str | None:
        if posting.comp is None or posting.comp.floor_value is None:
            return None
        return str(posting.comp.floor_value)


BUILTINS: dict[str, object] = {
    "freshness": _Freshness(),
    "region": _Region(),
    "remote": _Remote(),
    "comp_floor": _CompFloor(),
}
