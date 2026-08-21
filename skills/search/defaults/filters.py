"""User-owned filter predicates — copied to .agents/search/filters.py on first run.

Each predicate is ``fn(posting: Posting) -> bool``: return ``True`` to KEEP the
posting, ``False`` to drop it. ``config.yaml`` names which of these run, in
``filters:`` (before enrichment) or ``post_enrichment_filters:`` (after, so they
may read ``posting.comp``).

Idiom: null-safe. A field that is ``None`` means "unknown", and unknown passes —
no evidence means no reason to drop. Write predicates so a missing field can
never raise and never drop: coerce with ``(posting.field or "")`` before
testing.

The pipeline records every elimination as ``filtered:<name>``; user predicates
record the bare name only (the pipeline cannot know what your code judged on),
so a renamed predicate orphans its old ledger rows until they expire.
"""

from pipeline.model import Posting


def not_agency(posting: Posting) -> bool:
    """Keep unless the company name looks like a staffing/recruiting agency.

    ``(posting.company or "")`` turns a ``None`` company into ``""``, which
    matches no marker, so an unknown company is kept (pass-on-unknown).
    """
    company = (posting.company or "").lower()
    for marker in ("staffing", "recruiting", "agency", "talent", "consulting"):
        if marker in company:
            return False
    return True


def excludes_contract(posting: Posting) -> bool:
    """Keep unless the title signals a contract/temporary engagement.

    Same null-safe idiom: a ``None`` title becomes ``""`` and is kept.
    """
    title = (posting.title or "").lower()
    for marker in ("contract", "contractor", "temporary", "freelance", "c2c"):
        if marker in title:
            return False
    return True
