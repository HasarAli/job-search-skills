"""Stage 4 · compensation enrichment.

Re-exports the three comp submodules: ``enrich`` (the cascade orchestrator —
call ``enrich.enrich(...)``), ``levels`` (Levels.fyi ``.md`` client), and
``visa_wages`` (US visa-wage lookup, also runnable as a CLI via
``python -m pipeline.comp.visa_wages --refresh``).

The re-exports are lazy (PEP 562) so that ``python -m pipeline.comp.visa_wages``
does not re-execute an already-imported module.
"""

from __future__ import annotations

import importlib

__all__ = ["enrich", "levels", "visa_wages"]


def __getattr__(name: str):
    if name in __all__:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
