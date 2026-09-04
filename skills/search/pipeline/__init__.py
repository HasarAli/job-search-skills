"""The job search pipeline: shared types, config, sources, store, comp, output."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared" / "lib"))

__all__: list[str] = []
