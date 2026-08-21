"""Shared vocabulary for the job search pipeline.

These dataclasses are the contract every adapter, filter, and stage hands
around. ``Posting.to_dict()`` is the only place that knows the JSON field names
emitted to the shortlist (``pipeline/output.py`` serialises whatever it returns,
so keep these keys stable).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CompRange:
    min: float | None = None
    max: float | None = None
    currency: str | None = None

    def to_dict(self) -> dict:
        return {"min": self.min, "max": self.max, "currency": self.currency}


@dataclass
class CompLevel:
    name: str                # "L4", "IC3", ...
    total_comp: float        # median total comp
    currency: str

    def to_dict(self) -> dict:
        return {"name": self.name, "total_comp": self.total_comp, "currency": self.currency}


@dataclass
class CompRecord:
    provenance: str          # "stated" | "levels" | "visa-wages" | "none"
    floor_value: float | None   # lowest level's median (or stated min); None only when provenance=="none"
    currency: str | None
    ladder: list[CompLevel] | None   # None for "none"; [] allowed for stated
    range: CompRange | None          # set for "stated"
    employer: str | None             # matched employer name for levels/visa-wages

    def to_dict(self) -> dict:
        return {
            "provenance": self.provenance,
            "floor_value": self.floor_value,
            "currency": self.currency,
            "ladder": [level.to_dict() for level in self.ladder] if self.ladder is not None else None,
            "range": self.range.to_dict() if self.range is not None else None,
            "employer": self.employer,
        }


@dataclass
class Posting:
    source: str              # adapter name, e.g. "greenhouse"
    source_id: str           # stable source id, MANDATORY (identity)
    title: str
    company: str
    url: str
    location: str | None = None
    remote: bool | None = None    # True/False/None(unknown)
    posted_at: datetime | None = None   # OPTIONAL per 004
    stated_comp: CompRange | None = None
    comp: CompRecord | None = None      # filled by enrichment

    def to_dict(self) -> dict:
        """JSON-safe dict. Dates become ISO8601 strings; nested records recurse.

        This is the single source of truth for shortlist field names — extra
        fields may appear as sources are added, but these keys are the stub.
        """
        return {
            "source": self.source,
            "source_id": self.source_id,
            "title": self.title,
            "company": self.company,
            "url": self.url,
            "location": self.location,
            "remote": self.remote,
            "posted_at": self.posted_at.isoformat() if self.posted_at is not None else None,
            "stated_comp": self.stated_comp.to_dict() if self.stated_comp is not None else None,
            "comp": self.comp.to_dict() if self.comp is not None else None,
        }


@dataclass
class Query:
    roles: list[str]         # non-empty search terms
    region: str              # required
    remote: bool | None = None
    posted_since: datetime | None = None


@dataclass
class Failure:
    source: str
    tenant: str | None       # None = adapter-level failure
    error: str

    def to_dict(self) -> dict:
        return {"source": self.source, "tenant": self.tenant, "error": self.error}
