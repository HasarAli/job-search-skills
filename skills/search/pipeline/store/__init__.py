"""Stage 2: dedup + comp cache (SQLite storage)."""

from .dedup import dedup
from search_shared.ledger import Ledger

__all__ = ["Ledger", "dedup"]
