"""``agent-json`` adapter — postings collected by a separate agent, handed in by path.

The file is a JSON list of objects, each carrying at minimum ``source``,
``source_id``, ``title``, ``company``, ``url`` (plus optional ``location`` /
``remote`` / ``posted_at`` / ``stated_comp``). The row's ``source`` declares
which board it came from and is copied verbatim onto the ``Posting``, so it
dedups against the board's own adapter; ``source_id`` is supplied like any other
adapter.

The path comes from the source block's ``path`` (the runner already overrides
it with ``--json``). Relative paths resolve against the search state dir
(``$SEARCH_STATE_DIR``, default ``.agents/search/``). A
missing file, bad JSON, or a non-list document is one adapter-level
:class:`Failure`. There is deliberately **no staleness/max-age check** — handing
the file in IS the freshness decision, so ``posted_since`` is not applied here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.config import state_dir
from pipeline.model import CompRange, Failure, Posting, Query
from pipeline.sources.base import (
    BaseAdapter,
    coerce_bool,
    coerce_datetime,
    coerce_float,
    filter_locally,
    none_if_na,
)


class AgentJsonAdapter(BaseAdapter):
    name = "agent-json"

    def __init__(self, block: dict[str, Any]) -> None:
        self.path = block.get("path") or ""

    # -- Adapter -------------------------------------------------------------

    def list(self, query: Query) -> tuple[list[Posting], list[Failure]]:
        raw_path = str(self.path or "").strip()
        if not raw_path:
            return [], [
                Failure(
                    source=self.name,
                    tenant=None,
                    error="no input file path (set `path` on the agent-json source block or pass --json)",
                )
            ]

        path = self._resolve(raw_path)
        if not path.is_file():
            return [], [Failure(source=self.name, tenant=None, error=f"file not found: {path}")]

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return [], [Failure(source=self.name, tenant=None, error=f"{type(exc).__name__}: {exc}")]

        if not isinstance(data, list):
            return [], [
                Failure(
                    source=self.name,
                    tenant=None,
                    error=f"expected a JSON list of postings, got {type(data).__name__}",
                )
            ]

        postings: list[Posting] = []
        for row in data:
            posting = self._to_posting(row)
            if posting is not None:
                postings.append(posting)

        # Role/region/remote still apply (ordinary source); freshness does not —
        # handing the file in is the user's freshness decision.
        return filter_locally(postings, query, apply_freshness=False), []

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _resolve(raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = state_dir() / path
        return path

    @staticmethod
    def _to_posting(row: Any) -> Posting | None:
        if not isinstance(row, dict):
            return None
        source = none_if_na(row.get("source"))
        source_id = none_if_na(row.get("source_id"))
        if source is None or source_id is None or not str(source).strip() or not str(source_id).strip():
            return None
        return Posting(
            source=str(source).strip(),
            source_id=str(source_id).strip(),
            title=none_if_na(row.get("title")) or "",
            company=none_if_na(row.get("company")) or "",
            url=none_if_na(row.get("url")) or "",
            location=none_if_na(row.get("location")),
            remote=coerce_bool(row.get("remote")),
            posted_at=coerce_datetime(row.get("posted_at")),
            stated_comp=AgentJsonAdapter._comp(row.get("stated_comp")),
        )

    @staticmethod
    def _comp(value: Any) -> CompRange | None:
        if isinstance(value, CompRange):
            return value
        if not isinstance(value, dict):
            return None
        mn = coerce_float(value.get("min"))
        mx = coerce_float(value.get("max"))
        currency = value.get("currency")
        if mn is None and mx is None and not currency:
            return None
        return CompRange(min=mn, max=mx, currency=str(currency) if currency else None)
