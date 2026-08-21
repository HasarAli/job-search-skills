"""Source adapters — the config-driven collection stage.

``build_adapters(config)`` turns the explicit ``sources:`` list into adapter
instances; each adapter normalises everything it scrapes to
:class:`pipeline.model.Posting` and reports problems per tenant via
:class:`pipeline.model.Failure`.
"""

from pipeline.sources.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter, WorkdayAdapter
from pipeline.sources.base import Adapter, BaseAdapter
from pipeline.sources.feed import WwrAdapter
from pipeline.sources.jobspy import JobSpyAdapter
from pipeline.sources.jsonfile import AgentJsonAdapter
from pipeline.sources.registry import build_adapters

__all__ = [
    "Adapter",
    "BaseAdapter",
    "build_adapters",
    "JobSpyAdapter",
    "GreenhouseAdapter",
    "AshbyAdapter",
    "LeverAdapter",
    "WorkdayAdapter",
    "WwrAdapter",
    "AgentJsonAdapter",
]
