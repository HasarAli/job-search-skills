"""Record company evidence during a run, label postings, and back the CLI.

* :meth:`CompanyCheck.harvest` takes free evidence from everything a run
  collected: home-located roles and home-currency pay, plus every row of every
  configured board (so a configured company's label refreshes each run).
* :meth:`CompanyCheck.check` labels the postings that survived the filters,
  running an active check for companies that are due, and decides which
  postings the label rules out. The active check finds and reads the company's
  board; if that doesn't confirm it, it searches LinkedIn for the company's
  jobs in the home country (this covers companies on their own careers sites).
* :meth:`CompanyCheck.check_company` is one company on demand, for the CLI and
  the browser search.

Placement: a home-located posting always stays. A posting whose own text limits
it to another country is cut. A posting from a ``no`` company is cut. Every
other posting stays and carries its company's label for the shortlist.
"""

from __future__ import annotations

import re
from typing import Any

from pipeline.companies import boards
from pipeline.companies.evidence import BOARD_DETAILS_PER_KIND, Matcher
from pipeline.companies.settings import CheckSettings
from pipeline.http import DeadlineExceeded, HttpClient
from pipeline.sources.linkedin import LinkedInAdapter
from search_shared import companies as rules
from search_shared.ledger import Ledger
from search_shared.model import Failure, Posting

_SUMMARY_ITEMS = 2
_SUMMARY_CHARS = 180
_COMPANY_PAGE_RE = re.compile(r"linkedin\.com/company/([^/?#]+)", re.IGNORECASE)


def _company_page(url: str | None) -> str | None:
    """A LinkedIn company page's handle ("sift-stack"), whatever sub-page the link is on."""
    m = _COMPANY_PAGE_RE.search(url or "")
    return m.group(1).casefold() if m else None


def summarise(company: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The fresh evidence behind the label, most recent first."""
    if not company:
        return []
    deciding = {
        "confirmed": rules.HIGH, "no": rules.NEGATIVE, "likely": rules.CIRCUMSTANTIAL,
    }.get(company["label"], ())
    fresh = rules.fresh_kinds(company["evidence"])
    picked = [e for e in company["evidence"] if e["kind"] in deciding and e["kind"] in fresh]
    out = []
    for item in picked[:_SUMMARY_ITEMS]:
        detail = item["detail"]
        if len(detail) > _SUMMARY_CHARS:
            detail = detail[: _SUMMARY_CHARS - 1] + "…"
        out.append({"kind": item["kind"], "detail": detail, "url": item["url"], "seen_at": item["seen_at"][:10]})
    return out


class CompanyCheck:
    def __init__(self, settings: CheckSettings, ledger: Ledger, http: HttpClient) -> None:
        self.settings = settings
        self.ledger = ledger
        self.http = http
        self.matcher = Matcher(settings)
        self.failures: list[Failure] = []
        self._checked: set[str] = set()
        self._out_of_time = False

    # -- free evidence ---------------------------------------------------------

    def _board_evidence(self, platform: str, slug: str, rows: list[dict[str, Any]]) -> tuple[list[tuple], bool]:
        """Evidence from a board's rows, plus whether the reading was complete.

        When the listing shows nothing high-confidence, the board's own search
        for the home country runs too (Workday's listing stops at 2000 rows).
        A failed search makes the reading incomplete.
        """
        found = self.matcher.board_evidence(platform, slug, rows)
        if any(kind in rules.HIGH for kind, _, _ in found):
            return found, True
        try:
            extra = boards.search_rows(platform, slug, self.settings.home, self.http)
        except DeadlineExceeded:
            raise
        except Exception:  # noqa: BLE001 — a failed search leaves the reading incomplete
            return found, False
        if extra:
            found += self.matcher.board_evidence(platform, slug, extra)
        return found, True

    def harvest(self, postings: list[Posting], adapters: list[Any]) -> set[str]:
        """Record evidence from a run's collection; return the boards read in full."""
        rows: list[tuple] = []
        scanned: set[str] = set()
        for adapter in adapters:
            for tenant, board_rows in (getattr(adapter, "scanned", None) or {}).items():
                board = f"{adapter.name}:{tenant}"
                name = self.ledger.company_for_board(board) or boards.board_company_name(adapter.name, tenant, board_rows)
                self.ledger.set_company_board(name, board)
                self.ledger.mark_company_checked(name)
                try:
                    found, complete = self._board_evidence(adapter.name, tenant, board_rows)
                except DeadlineExceeded:
                    found, complete = self.matcher.board_evidence(adapter.name, tenant, board_rows), False
                rows.extend((name, kind, detail, url, None) for kind, detail, url in found)
                if complete:
                    scanned.add(board)
        for posting in postings:
            if posting.company.strip():
                rows.extend(self._posting_evidence(posting))
        self.ledger.record_evidence_many(rows)
        return scanned

    def _posting_evidence(self, posting: Posting, text: str | None = None) -> list[tuple]:
        name = posting.company.strip()
        rows = [(name, kind, f"{posting.title} — {detail}", posting.url or None, None)
                for kind, detail in self.matcher.location_evidence(posting.location)]
        comp = posting.stated_comp
        if comp is not None and self.matcher.is_home_currency(comp.currency):
            rows.append((name, "home_pay", f"{posting.title} — pay in {comp.currency.upper()}", posting.url or None, None))
        rows.extend((name, kind, detail, posting.url or None, None)
                    for kind, detail in self.matcher.text_evidence(text))
        return rows

    # -- active check -----------------------------------------------------------

    def _active_check(
        self, name: str, title: str | None, hint: tuple[str, str] | None, company_url: str | None = None,
    ) -> None:
        """Read the company's board, then LinkedIn if needed; stamp the check either way."""
        company = self.ledger.company(name)
        key = company["key"] if company else rules.normalise_name(name)
        if key in self._checked or self._out_of_time:
            return
        self._checked.add(key)
        if hint is None and company and company["board"]:
            platform, _, slug = company["board"].partition(":")
            hint = (platform, slug)
        # A company's own careers site can't be read, but it may still embed a
        # readable board: guess, and fall back to recording the site.
        custom = hint if hint is not None and hint[0] == "custom" else None
        try:
            board = boards.find_board(name, title, self.http, hint=None if custom else hint)
        except DeadlineExceeded as exc:
            self._out_of_time = True
            self.failures.append(Failure(source="company_check", tenant=name, error=str(exc)))
            return
        if board is None and custom is not None:
            board = boards.Board(*custom)
        if board is not None:
            self.ledger.set_company_board(name, board.ref)
            if board.rows is not None:
                try:
                    found, _ = self._board_evidence(board.platform, board.slug, board.rows)
                except DeadlineExceeded as exc:
                    self._out_of_time = True
                    self.failures.append(Failure(source="company_check", tenant=name, error=str(exc)))
                    found = self.matcher.board_evidence(board.platform, board.slug, board.rows)
                self.ledger.record_evidence_many((name, kind, detail, url, None) for kind, detail, url in found)
            elif board.readable:
                self.failures.append(Failure(source="company_check", tenant=name, error=f"could not read {board.ref}"))
        current = self.ledger.company(name)
        if not self._out_of_time and (current is None or current["label"] != "confirmed"):
            self._linkedin_check(name, company_url)
        self.ledger.mark_company_checked(name)

    def _linkedin_check(self, name: str, company_url: str | None) -> None:
        """Search LinkedIn for the company's jobs located in the home country.

        A result counts only when it is the same company: the same LinkedIn
        company page when one is known, else the same normalised name.
        """
        if self.settings.linkedin_geo_id is None:
            return
        try:
            cards = LinkedInAdapter({"name": "linkedin"}, http=self.http).company_jobs(
                name, self.settings.linkedin_geo_id)
        except DeadlineExceeded as exc:
            self._out_of_time = True
            self.failures.append(Failure(source="company_check", tenant=name, error=str(exc)))
            return
        except Exception as exc:  # noqa: BLE001 — a failed search leaves the label as it was
            self.failures.append(Failure(source="company_check", tenant=name, error=f"LinkedIn search: {exc}"))
            return
        key = rules.normalise_name(name)
        page = _company_page(company_url)
        found: list[tuple] = []
        for card in cards:
            card_page = _company_page(card.company_url)
            if page and card_page:
                same = card_page == page
            else:
                same = rules.normalise_name(card.company) == key
            if not same:
                continue
            for kind, detail in self.matcher.location_evidence(card.location):
                found.append((name, kind, f"{card.title} — {detail} (LinkedIn)", card.url.split("?")[0], None))
        self.ledger.record_evidence_many(found[:BOARD_DETAILS_PER_KIND])

    # -- labelling a run's postings --------------------------------------------

    def check(self, postings: list[Posting], descriptions: dict[int, str]) -> tuple[list[Posting], list[tuple[Posting, str]]]:
        """Label each posting; return ``(kept, [(cut posting, reason)])``."""
        kept: list[Posting] = []
        cut: list[tuple[Posting, str]] = []
        for posting in postings:
            reason = self._check_posting(posting, descriptions.get(id(posting)))
            if reason is None:
                kept.append(posting)
            else:
                cut.append((posting, reason))
        return kept, cut

    def _check_posting(self, posting: Posting, text: str | None) -> str | None:
        name = posting.company.strip()
        home = self.matcher.is_home(posting.location)
        if not name:
            posting.company_check = self._info(None, home)
            return None
        evidence = self._posting_evidence(posting, text)
        self.ledger.record_evidence_many(evidence)
        company = self.ledger.company(name)
        if company is None or company["due"]:
            hint = boards.parse_board_url(posting.url)
            if posting.board:
                platform, _, slug = posting.board.partition(":")
                hint = (platform, slug)
            self._active_check(name, posting.title, hint, posting.company_url)
            company = self.ledger.company(name)
        posting.company_check = self._info(company, home)
        if home:
            return None
        away = [detail for _, kind, detail, _, _ in evidence if kind == "away_only"]
        if away:
            return f"posting limits the role to another country: {away[0]}"
        if company and company["label"] == "no":
            items = summarise(company)
            return "company: no" + (f" — {items[0]['detail']}" if items else "")
        return None

    def _info(self, company: dict[str, Any] | None, home: bool) -> dict[str, Any]:
        label = company["label"] if company else "unknown"
        return {
            "home": self.settings.home,
            "label": label,
            "posting_in_home": home,
            "board": company["board"] if company else None,
            "evidence": summarise(company),
            "people_check": (not home and label == "unknown" and self.settings.linkedin_geo_id is not None),
        }

    # -- one company on demand --------------------------------------------------

    def check_company(
        self,
        name: str,
        *,
        title: str | None = None,
        url: str | None = None,
        location: str | None = None,
        text: str | None = None,
        company_url: str | None = None,
        force: bool = False,
    ) -> dict[str, Any] | None:
        """Record what the caller observed, run an active check if due (or forced)."""
        posting = Posting(source="cli", source_id="-", title=title or "", company=name,
                          url=url or "", location=location)
        self.ledger.record_evidence_many(self._posting_evidence(posting, text))
        company = self.ledger.company(name)
        if force or company is None or company["due"]:
            self._active_check(name, title, boards.parse_board_url(url), company_url)
            company = self.ledger.company(name)
        return company
