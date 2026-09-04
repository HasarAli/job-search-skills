"""Entry point for Search's scripted-source mode.

Stage order (spec — search.py section + Testing section)::

  1. config.load_config()                 structural errors -> stderr JSON, exit 2
  2. sources.registry.build_adapters(config)
  3. collect (runner-owned per-adapter timeout; sequential in v1)
  4. store.dedup.dedup(...)
  5. pushdown re-check (freshness/region/remote) -> contract violations
  6. cheap filters (config.filters only; the built-ins ran at stage 5)
  6b. JD fetch (adapter.fetch_detail for salary; linkedin only)
  7. comp.enrich.enrich(...)
  8. post-enrich filters (config.post_enrichment_filters + comp_floor)
  9. output.emit(...) to stdout; ledger.record_sightings(...) in ONE transaction
 10. exit 0 (shortlist produced) / 1 (zero sources reached) / 2 (structural)

One small function per stage; ``main()`` is the only thing that calls them in
order. Nothing here implements stage behaviour — the sibling modules under
``pipeline/`` own it; this module only wires their exact call sites.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pipeline.comp import visa_wages as wages_cli
from pipeline.comp.enrich import enrich
from pipeline.config import Config, ConfigError, load_config, load_filters
from pipeline.filters import BUILTINS
from search_shared.model import Failure, Posting
from pipeline.output import emit
from pipeline.http import DeadlineExceeded, HttpClient
from pipeline.sources.registry import build_adapters
from pipeline.store.dedup import dedup
from search_shared.ledger import Ledger

#: Cooperative budget per adapter ``list()`` call (seconds). Adapters check the
#: shared client's monotonic budget between requests; no worker is left running
#: after a timeout.
ADAPTER_TIMEOUT = 1800.0

#: Sentinel meaning "this filter predicate takes a posting only" (no ``arg``).
_NO_ARG = object()

# ---- stage helpers ---------------------------------------------------------


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="search script",
        description="Run the config-driven job search pipeline",
    )
    parser.add_argument(
        "--config", metavar="PATH",
        help="path to config.yaml (default: $SEARCH_STATE_DIR/config.yaml)",
    )
    parser.add_argument(
        "--json", metavar="PATH", dest="json_path",
        help="override the agent-json source's input file path",
    )
    parser.add_argument(
        "--refresh-visa-wages", action="store_true",
        help="refresh the US visa-wage dataset, then exit (delegates to pipeline.comp.visa_wages)",
    )
    return parser.parse_args(argv)


def _apply_json_override(config: Config, json_path: str | None) -> None:
    """``--json PATH`` overrides the agent-json source's input path (spec)."""
    if not json_path:
        return
    for source in config.sources:
        if source.get("name") == "agent-json":
            source["path"] = json_path
            break


def _failure_from_exception(adapter: Any, exc: BaseException) -> Failure:
    """Normalize transport/adapter exceptions into the observable contract."""
    return Failure(
        source=adapter.name,
        tenant=None,
        error=f"{type(exc).__name__}: {exc}",
    )


def _run_adapter(adapter: Any, query: Any, http: Any, timeout: float) -> Any:
    """Run one adapter synchronously inside its cooperative HTTP budget."""
    try:
        with http.budget(timeout):
            return adapter.list(query)
    except Exception as exc:  # noqa: BLE001 — isolate a misbehaving adapter
        return [], [_failure_from_exception(adapter, exc)]


def _collect(
    adapters: list, query: Any, http: Any, timeout: float
) -> tuple[list[Posting], list[Failure], list[str]]:
    """Stage 3: run every adapter in series, accumulate postings and failures.

    Returns ``(postings, failures, zero_result_adapter_names)``.
    """
    postings: list[Posting] = []
    failures: list[Failure] = []
    zero_names: list[str] = []

    for adapter in adapters:
        result = _run_adapter(adapter, query, http, timeout)
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and all(isinstance(x, list) for x in result)
        ):
            ps, fs = result
        else:
            failures.append(
                Failure(
                    source=adapter.name,
                    tenant=None,
                    error=f"bad return shape: {type(result).__name__}",
                )
            )
            zero_names.append(adapter.name)
            continue
        postings.extend(ps)
        failures.extend(fs)
        if not ps:
            zero_names.append(adapter.name)

    return postings, failures, zero_names


def _report_failures(failures: list[Failure]) -> None:
    """Console line per failure: ``source <name>: <error>`` (tenant if set)."""
    for failure in failures:
        name = failure.source if failure.tenant is None else f"{failure.source}[{failure.tenant}]"
        print(f"source {name}: {failure.error}", file=sys.stderr)


def _report_zero_results(zero_names: list[str]) -> None:
    """Unconditional zero-results warning per adapter that returned nothing.

    Never affects the exit code.
    """
    for name in zero_names:
        print(f"zero results: {name}", file=sys.stderr)


def _apply(fn: Any, posting: Posting, arg: Any = _NO_ARG) -> bool:
    """Call a built-in/user predicate with or without its extra ``arg``."""
    if arg is _NO_ARG:
        return fn(posting)
    return fn(posting, arg)


def _pushdown_checks(
    query: Any, posting: Posting,
) -> list[tuple[str, Any, Any]]:
    """The pushdown predicates re-checked after collection, in order.

    Freshness is skipped for prescreened postings (004 rules that handing the
    file in IS the freshness decision) and for skip_freshness postings (ATS
    boards list all-open roles). Both flags travel on the posting itself.
    """
    checks: list[tuple[str, Any, Any]] = []
    if query.posted_since is not None and not posting.prescreened and not posting.skip_freshness:
        checks.append(("freshness", BUILTINS["freshness"], query.posted_since))
    checks.append(("region", BUILTINS["region"], query.region))
    checks.append(("remote", BUILTINS["remote"], _NO_ARG))
    return checks


def _recheck_pushdown(
    postings: list[Posting], query: Any,
) -> list[Posting]:
    """Stage 5: re-apply freshness/region/remote to every unseen posting.

    Adapters are responsible for these, so a drop here is a contract violation:
    printed as ``contract_violation:<source>:<name>`` and NOT recorded.
    """
    kept: list[Posting] = []
    for posting in postings:
        for name, fn, arg in _pushdown_checks(query, posting):
            if not _apply(fn, posting, arg):
                print(f"contract_violation:{posting.source}:{name}", file=sys.stderr)
                break
        else:
            kept.append(posting)
    return kept


def _sighting_row(posting: Posting, outcome: str, reason: str | None = None) -> tuple:
    """Denormalise one posting into a 9-tuple for ``record_sightings``."""
    return (
        posting.source, posting.source_id, None, outcome, reason,
        posting.company, posting.title, posting.url, None,
    )


def _run_filters(
    postings: list[Posting],
    stages: list[tuple[str, Any, Any, bool]],
) -> tuple[list[Posting], list[tuple]]:
    """Run ordered filter stages; drop the first non-match, record it.

    ``stages`` entries are ``(name, fn, arg, is_builtin)``. Returns
    ``(survivors, elimination_rows)`` — eliminations are 9-tuples ready for
    ``record_sightings`` (built-ins record their observed value via
    ``describe``; user filters record ``None``).
    """
    survivors: list[Posting] = []
    eliminations: list[tuple] = []
    for posting in postings:
        for name, fn, arg, is_builtin in stages:
            if _apply(fn, posting, arg):
                continue
            reason = fn.describe(posting) if is_builtin else None
            eliminations.append(_sighting_row(posting, f"filtered:{name}", reason))
            break
        else:
            survivors.append(posting)
    return survivors, eliminations


def _cheap_filters(
    postings: list[Posting], config: Config, user_filters: dict[str, Any]
) -> tuple[list[Posting], list[tuple]]:
    """Stage 6: ``config.filters`` only.

    The built-in freshness/region/remote predicates already ran at stage 5
    (the pushdown re-check); applying them here again would be dead code.
    """
    stages: list[tuple[str, Any, Any, bool]] = []
    for name in config.filters:
        stages.append((name, user_filters[name], _NO_ARG, False))
    return _run_filters(postings, stages)


def _post_enrich_filters(
    postings: list[Posting], config: Config, user_filters: dict[str, Any]
) -> tuple[list[Posting], list[tuple]]:
    """Stage 8: built-in ``comp_floor``, then ``config.post_enrichment_filters``."""
    stages: list[tuple[str, Any, Any, bool]] = []
    if config.comp_floor is not None:
        stages.append(("comp_floor", BUILTINS["comp_floor"], config.comp_floor, True))
    for name in config.post_enrichment_filters:
        stages.append((name, user_filters[name], _NO_ARG, False))
    return _run_filters(postings, stages)


def _fetch_details(postings: list[Posting], adapters: list) -> tuple[dict[int, str], list[Failure]]:
    """Stage 6b: fetch each cheap-filter survivor's description, for salary.

    Only ``linkedin`` implements ``fetch_detail`` (others return ``None``).
    Returns descriptions plus failures. A bad detail page only affects that
    posting; collection and healthy postings continue.
    """
    by_name = {adapter.name: adapter for adapter in adapters}
    descriptions: dict[int, str] = {}
    failures: list[Failure] = []
    for posting in postings:
        adapter = by_name.get(posting.source)
        if adapter is None:
            continue
        try:
            description = adapter.fetch_detail(posting)
        except DeadlineExceeded as exc:
            failures.append(_failure_from_exception(adapter, exc))
            break
        except Exception as exc:  # noqa: BLE001 — a bad JD must not sink the posting
            failure = _failure_from_exception(adapter, exc)
            failure.error = f"detail {posting.source_id}: {failure.error}"
            failures.append(failure)
            continue
        if description:
            descriptions[id(posting)] = description
    return descriptions, failures


def _exit_code(survivors: list[Posting], adapters: list, postings: list[Posting]) -> int:
    """Stage 10: 0 if a shortlist was produced, else 1 on a total failure.

    "Zero sources reached" = at least one adapter existed and nothing was
    collected. Sources reached but everything filtered/deduped out is a valid
    (empty) shortlist, not a failure.
    """
    if survivors:
        return 0
    if adapters and not postings:
        return 1
    return 0


# ---- the pipeline ----------------------------------------------------------


def _run_pipeline(config: Config, args: argparse.Namespace) -> int:
    _apply_json_override(config, args.json_path)

    # 2. Adapters from the explicit ``sources:`` list.
    http = HttpClient()

    # Shared host state keeps blocks active across collection and enrichment.
    with http:
        adapters = build_adapters(config, http=http)

        # 3. Collect, then report failures and zero-result adapters (console only).
        postings, failures, zero_names = _collect(adapters, config.query, http, ADAPTER_TIMEOUT)
        _report_zero_results(zero_names)

        ledger = Ledger(config.seen_db_path)
        unseen = dedup(postings, ledger)
        after_recheck = _recheck_pushdown(unseen, config.query)
        user_filters = load_filters()
        cheap_survivors, cheap_eliminations = _cheap_filters(after_recheck, config, user_filters)
        with http.budget(ADAPTER_TIMEOUT):
            descriptions, detail_failures = _fetch_details(cheap_survivors, adapters)
        failures.extend(detail_failures)
        with http.budget(ADAPTER_TIMEOUT):
            enrich(cheap_survivors, config, ledger, descriptions, http=http, failures=failures)
        survivors, post_eliminations = _post_enrich_filters(cheap_survivors, config, user_filters)

        eliminations = cheap_eliminations + post_eliminations
        counts = {
            "collected": len(postings),
            "unseen": len(unseen),
            "filtered": len(eliminations),
            "enriched": sum(1 for p in cheap_survivors if p.comp is not None),
            "emitted": len(survivors),
        }
        _report_failures(failures)
        emit(survivors, config, counts)
        rows = list(eliminations)
        for posting in survivors:
            rows.append(_sighting_row(posting, "shortlisted"))
        ledger.record_sightings(rows)
        return _exit_code(survivors, adapters, postings)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.refresh_visa_wages:
        # Delegate to the visa-wage CLI: python -m pipeline.comp.visa_wages --refresh
        return wages_cli.main(["--refresh"])

    # 1. Config load + structural validation — refuses before any network call.
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        for error in exc.errors:
            print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2

    return _run_pipeline(config, args)


if __name__ == "__main__":
    raise SystemExit(main())
