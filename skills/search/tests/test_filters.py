"""Built-in predicates — pass-on-unknown is the contract.

Each built-in must keep a posting whose relevant field is missing; it must drop
only on a clear non-match. Wrong here fails silently: a good job dropped, or a
bad one kept.
"""

from datetime import datetime, timedelta, timezone

import pytest

from pipeline.filters import BUILTINS
from pipeline.model import CompRecord, Posting

freshness = BUILTINS["freshness"]
region = BUILTINS["region"]
remote = BUILTINS["remote"]
comp_floor = BUILTINS["comp_floor"]

NOW = datetime.now(timezone.utc)


def _posting(**kw) -> Posting:
    defaults = dict(source="s", source_id="1", title="t", company="c", url="u")
    defaults.update(kw)
    return Posting(**defaults)


@pytest.mark.parametrize(
    "posted_at,since,expected",
    [
        (None, NOW, True),                                # undated passes
        (NOW, NOW - timedelta(days=1), True),             # fresh passes
        (NOW - timedelta(days=7), NOW, False),            # stale drops
    ],
)
def test_freshness(posted_at, since, expected):
    assert freshness(_posting(posted_at=posted_at), since) is expected


@pytest.mark.parametrize(
    "location,region_name,expected",
    [
        (None, "san francisco", True),                    # unknown passes
        ("San Francisco, CA", "san francisco", True),
        ("SAN FRANCISCO, CA", "san francisco", True),     # case-insensitive
        ("New York, NY", "san francisco", False),
    ],
)
def test_region(location, region_name, expected):
    assert region(_posting(location=location), region_name) is expected


@pytest.mark.parametrize(
    "remote_val,expected",
    [
        (None, True),                                     # unknown passes
        (True, True),
        (False, False),                                   # explicit non-remote drops
    ],
)
def test_remote(remote_val, expected):
    assert remote(_posting(remote=remote_val)) is expected


_COMP_250 = CompRecord(provenance="levels", floor_value=250000.0, currency="USD",
                       ladder=None, range=None, employer=None)
_COMP_150 = CompRecord(provenance="levels", floor_value=150000.0, currency="USD",
                       ladder=None, range=None, employer=None)
_COMP_UNKNOWN = CompRecord(provenance="none", floor_value=None, currency=None,
                           ladder=None, range=None, employer=None)


@pytest.mark.parametrize(
    "comp,floor,expected",
    [
        (None, 200000, True),                             # no comp info passes
        (_COMP_UNKNOWN, 200000, True),                    # unknown floor passes
        (_COMP_250, 200000, True),                        # above floor passes
        (_COMP_150, 200000, False),                       # known below floor drops
    ],
)
def test_comp_floor(comp, floor, expected):
    assert comp_floor(_posting(comp=comp), floor) is expected
