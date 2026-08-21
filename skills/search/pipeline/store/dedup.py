"""Dedup policy: drop postings the ledger has seen, or that repeat this run."""

from ..model import Posting
from .ledger import Ledger


def dedup(postings: list[Posting], ledger: Ledger) -> list[Posting]:
    """Return ``postings`` minus anything already sighted.

    A posting is dropped when its ``(source, source_id)`` identity is either in
    the ledger (:meth:`Ledger.is_seen`) or already seen earlier in the same run
    (an in-run identity set). Order of the survivors is preserved.
    """
    seen: set[tuple[str, str]] = set()
    kept: list[Posting] = []
    for posting in postings:
        identity = (posting.source, posting.source_id)
        if identity in seen:
            continue
        seen.add(identity)
        if ledger.is_seen(posting.source, posting.source_id):
            continue
        kept.append(posting)
    return kept
