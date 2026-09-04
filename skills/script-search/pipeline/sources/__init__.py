"""Source adapters — the config-driven collection stage.

``build_adapters(config)`` turns the explicit ``sources:`` list into adapter
instances; each adapter normalises everything it scrapes to
:class:`search_shared.model.Posting` and reports problems per tenant via
:class:`search_shared.model.Failure`.
"""

from pipeline.sources.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter, WorkdayAdapter
from pipeline.sources.base import Adapter, BaseAdapter
from pipeline.sources.feed import WwrAdapter
from pipeline.sources.jsonfile import AgentJsonAdapter
from pipeline.sources.linkedin import LinkedInAdapter
from pipeline.sources.registry import build_adapters

__all__ = [
    "Adapter",
    "BaseAdapter",
    "build_adapters",
    "LinkedInAdapter",
    "GreenhouseAdapter",
    "AshbyAdapter",
    "LeverAdapter",
    "WorkdayAdapter",
    "WwrAdapter",
    "AgentJsonAdapter",
]
