"""Entry point for the job search pipeline (``search`` console script).

Stage order (spec — search.py section + Testing section)::

  1. config.load_config()                 structural errors -> stderr JSON, exit 2
  2. sources.registry.build_adapters(config)
  3. collect (runner-owned per-adapter timeout; sequential in v1)
  4. store.dedup.dedup(...)
  5. pushdown re-check (freshness/region/remote) -> contract violations
  6. cheap filters (config.filters only; the built-ins ran at stage 5)
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
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from pipeline.comp import visa_wages as wages_cli
from pipeline.comp.enrich import enrich
from pipeline.config import Config, ConfigError, load_config, load_filters
from pipeline.filters import BUILTINS
from pipeline.model import Failure, Posting
from pipeline.output import emit
from pipeline.sources.registry import build_adapters
from pipeline.store.dedup import dedup
from pipeline.store.ledger import Ledger

#: Runner-owned hard timeout per adapter ``list()`` call (seconds). Adapters own
#: retry/backoff; the runner only caps the wall-clock of the whole call.
ADAPTER_TIMEOUT = 60.0

#: The agent-json source is never freshness-checked (004: handing the file in
#: IS the freshness decision; staleness belongs to whoever invokes the run).
AGENT_JSON_SOURCE = "agent-json"

#: Sentinel meaning "this filter predicate takes a posting only" (no ``arg``).
_NO_ARG = object()

#: Sentinel returned by the collection stage when an adapter call timed out.
_TIMEOUT = object()


# ---- stage helpers ---------------------------------------------------------


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="search",
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


def _run_adapter(adapter: Any, query: Any, timeout: float) -> Any:
    """Run one ``adapter.list(query)`` under a runner-owned timeout.

    Returns the adapter's ``(postings, failures)`` tuple, ``_TIMEOUT`` on a
    timeout, or ``([], [one adapter-level Failure])`` if the adapter raised
    instead of reporting the failure itself.
    """
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="search-adapter")
    future = executor.submit(adapter.list, query)
    try:
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            future.cancel()
            return _TIMEOUT
        except Exception as exc:  # noqa: BLE001 — isolate a misbehaving adapter
            return [], [Failure(source=adapter.name, tenant=None, error=f"{type(exc).__name__}: {exc}")]
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _collect(
    adapters: list, query: Any, timeout: float
) -> tuple[list[Posting], list[Failure], list[str], set[tuple[str, str]]]:
    """Stage 3: run every adapter in series, accumulate postings and failures.

    Returns ``(postings, failures, zero_result_adapter_names,
    freshness_exempt)`` — the last is the ``(source, source_id)`` set of
    postings collected from the agent-json adapter, which is never
    freshness-checked (004).
    """
    postings: list[Posting] = []
    failures: list[Failure] = []
    zero_names: list[str] = []
    freshness_exempt: set[tuple[str, str]] = set()

    for adapter in adapters:
        result = _run_adapter(adapter, query, timeout)
        if result is _TIMEOUT:
            failures.append(
                Failure(source=adapter.name, tenant=None, error=f"timed out after {timeout:g}s")
            )
            zero_names.append(adapter.name)
            continue
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
        if getattr(adapter, "name", None) == AGENT_JSON_SOURCE:
            freshness_exempt.update((p.source, p.source_id) for p in ps)
        if not ps:
            zero_names.append(adapter.name)

    return postings, failures, zero_names, freshness_exempt


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
    query: Any, posting: Posting, freshness_exempt: set[tuple[str, str]]
) -> list[tuple[str, Any, Any]]:
    """The pushdown predicates re-checked after collection, in order.

    Freshness is skipped for postings collected from the agent-json adapter:
    004 rules that handing the file in IS the freshness decision, so those
    postings are never stale-checked. They are identified by their
    ``(source, source_id)`` identity — the agent-json adapter rewrites
    ``source`` to the board the row declares, so the adapter name is not on the
    posting.
    """
    checks: list[tuple[str, Any, Any]] = []
    if query.posted_since is not None and (posting.source, posting.source_id) not in freshness_exempt:
        checks.append(("freshness", BUILTINS["freshness"], query.posted_since))
    checks.append(("region", BUILTINS["region"], query.region))
    checks.append(("remote", BUILTINS["remote"], _NO_ARG))
    return checks


def _recheck_pushdown(
    postings: list[Posting], query: Any, freshness_exempt: set[tuple[str, str]]
) -> list[Posting]:
    """Stage 5: re-apply freshness/region/remote to every unseen posting.

    Adapters are responsible for these, so a drop here is a contract violation:
    printed as ``contract_violation:<source>:<name>`` and NOT recorded.
    """
    kept: list[Posting] = []
    for posting in postings:
        for name, fn, arg in _pushdown_checks(query, posting, freshness_exempt):
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
    adapters = build_adapters(config)

    # 3. Collect, then report failures and zero-result adapters (console only).
    postings, failures, zero_names, freshness_exempt = _collect(
        adapters, config.query, ADAPTER_TIMEOUT
    )
    _report_failures(failures)
    _report_zero_results(zero_names)

    ledger = Ledger(config.seen_db_path)

    # 4. Drop anything the ledger (or this run) has already sighted.
    unseen = dedup(postings, ledger)

    # 5. Pushdown re-check — drops are contract violations, never recorded.
    after_recheck = _recheck_pushdown(unseen, config.query, freshness_exempt)

    # 6. Cheap filters; every drop is recorded as ``filtered:<name>``.
    user_filters = load_filters()
    cheap_survivors, cheap_eliminations = _cheap_filters(after_recheck, config, user_filters)

    # 7. Compensation cascade — fills ``posting.comp`` in place.
    enriched = enrich(cheap_survivors, config, ledger)

    # 8. Post-enrichment filters (``comp_floor`` + user predicates).
    survivors, post_eliminations = _post_enrich_filters(enriched, config, user_filters)

    # 9. Counts, output envelope, then ONE atomic ledger write.
    eliminations = cheap_eliminations + post_eliminations
    counts = {
        "collected": len(postings),
        "unseen": len(unseen),
        "filtered": len(eliminations),
        # enrich sets posting.comp on every posting it sees (even provenance
        # "none"), so this is simply the count that reached the enrich stage.
        "enriched": sum(1 for p in enriched if p.comp is not None),
        "emitted": len(survivors),
    }
    emit(survivors, config, counts)

    rows = list(eliminations)
    for posting in survivors:
        rows.append(_sighting_row(posting, "shortlisted"))
    ledger.record_sightings(rows)  # atomic: a run that dies before here writes nothing

    # 10. Exit code.
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
