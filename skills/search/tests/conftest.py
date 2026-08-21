"""Make ``pipeline`` importable no matter where pytest is invoked from."""

import sys
from pathlib import Path

SEARCH_DIR = Path(__file__).resolve().parent.parent
if str(SEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(SEARCH_DIR))
