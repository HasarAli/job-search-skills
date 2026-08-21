"""Registry: the explicit ``sources:`` list -> adapter instances.

Not listed = not run. No auto-discovery. ``config.py`` already validates source
names and keys; this mapping is the defensive backstop and raises a
:class:`ConfigError` with the spec's structural-error shape if an unknown name
ever slips through.
"""

from __future__ import annotations

from typing import Any, Type

from pipeline.config import Config, ConfigError
from pipeline.sources.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter, WorkdayAdapter
from pipeline.sources.base import Adapter
from pipeline.sources.feed import WwrAdapter
from pipeline.sources.jobspy import JobSpyAdapter
from pipeline.sources.jsonfile import AgentJsonAdapter

#: Adapter key (``sources[].name``) -> adapter class taking its source block.
_ADAPTERS: dict[str, Type[Any]] = {
    "jobspy": JobSpyAdapter,
    "wwr": WwrAdapter,
    "greenhouse": GreenhouseAdapter,
    "ashby": AshbyAdapter,
    "lever": LeverAdapter,
    "workday": WorkdayAdapter,
    "agent-json": AgentJsonAdapter,
}


def build_adapters(config: Config) -> list[Adapter]:
    """Build one adapter per block in ``config.sources``, in config order."""
    adapters: list[Adapter] = []
    errors: list[dict[str, str]] = []

    for i, block in enumerate(config.sources):
        if not isinstance(block, dict):
            errors.append(
                {
                    "path": f"sources[{i}]",
                    "expected": "source block (mapping)",
                    "found": _found(block),
                }
            )
            continue
        name = block.get("name")
        cls = _ADAPTERS.get(name)
        if cls is None:
            errors.append(
                {
                    "path": f"sources[{i}].name",
                    "expected": f"one of {', '.join(sorted(_ADAPTERS))}",
                    "found": _found(name),
                }
            )
            continue
        adapters.append(cls(block))

    if errors:
        raise ConfigError(errors)
    return adapters


def _found(value: Any) -> str:
    """Mirror ``config.py``'s rendering of an observed value for ``found``."""
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    import json

    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(value)
