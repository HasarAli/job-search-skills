"""Dedup policy: drop postings the ledger has seen, or that repeat this run."""

from search_shared.model import Posting
from search_shared.ledger import Ledger


def dedup(postings: list[Posting], ledger: Ledger) -> list[Posting]:
    """Return ``postings`` minus anything already sighted (ledger or this run).

    One ledger call for the whole batch (:meth:`Ledger.unseen_identities`); order
    of survivors is preserved.
    """
    seen: set[tuple[str, str]] = set()
    identities: set[tuple[str, str]] = set()
    ordered: list[Posting] = []
    for posting in postings:
        identity = (posting.source, posting.source_id)
        if identity in seen:
            continue
        seen.add(identity)
        identities.add(identity)
        ordered.append(posting)
    unseen = ledger.unseen_identities(identities)
    return [p for p in ordered if (p.source, p.source_id) in unseen]
