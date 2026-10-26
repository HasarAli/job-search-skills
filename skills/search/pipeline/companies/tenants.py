"""Keep ``config.yaml``'s board lists in step with company labels.

:func:`plan` compares the ledger with the configured tenants:

* ``added`` — ``confirmed`` companies whose board is readable but not listed.
* ``removed`` — listed tenants whose board was read this run and whose company
  is no longer ``confirmed``. A board that failed to load is never removed.
* ``reader_needed`` — unreadable platforms (not custom sites) that at least
  :data:`READER_THRESHOLD` confirmed companies use.

:func:`apply` edits the file in place as text, so comments and layout
survive, then re-parses it and refuses to write anything but the intended
change.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from pipeline.companies.boards import READERS
from search_shared.ledger import Ledger

READER_THRESHOLD = 2

_TOP_KEY_RE = re.compile(r"^[^\s#-][^:]*:")
_ITEM_RE = re.compile(r"^(\s*)-\s+name:\s*[\"']?([\w-]+)[\"']?\s*(?:#.*)?$")
_TENANTS_RE = re.compile(r"^(\s*)tenants:\s*(.*)$")
_PLAIN_RE = re.compile(r"^[A-Za-z0-9][\w.\-]*$")


def _configured(sources: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for block in sources:
        name = block.get("name")
        if name in READERS:
            out.setdefault(name, []).extend(t for t in block.get("tenants") or [] if isinstance(t, str))
    return out


def plan(sources: list[dict[str, Any]], ledger: Ledger, scanned: set[str]) -> dict[str, Any]:
    configured = _configured(sources)
    listed = {f"{p}:{t}".casefold() for p, ts in configured.items() for t in ts}
    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    unreadable: dict[str, list[str]] = {}
    by_board: dict[str, dict[str, Any]] = {}
    for company in ledger.companies():
        board = company["board"]
        if not board:
            continue
        by_board[board.casefold()] = company
        if company["label"] != "confirmed":
            continue
        platform, _, slug = board.partition(":")
        if platform in READERS:
            if board.casefold() not in listed:
                added.setdefault(platform, []).append(slug)
        elif platform != "custom":
            unreadable.setdefault(platform, []).append(company["name"])
    for platform, tenants in configured.items():
        for slug in tenants:
            board = f"{platform}:{slug}"
            if board not in scanned:
                continue
            company = by_board.get(board.casefold())
            if company is None or company["label"] != "confirmed":
                removed.setdefault(platform, []).append(slug)
    reader_needed = {p: sorted(names) for p, names in unreadable.items() if len(names) >= READER_THRESHOLD}
    return {"added": added, "removed": removed, "reader_needed": reader_needed}


# ---- editing config.yaml ----------------------------------------------------


def _scalar(value: str) -> str:
    return value if _PLAIN_RE.match(value) else json.dumps(value)


def _section(lines: list[str]) -> tuple[int, int] | None:
    """``(first, end)`` line indexes of the ``sources:`` block."""
    for i, line in enumerate(lines):
        if re.match(r"^sources:\s*(#.*)?$", line):
            end = len(lines)
            for j in range(i + 1, len(lines)):
                if _TOP_KEY_RE.match(lines[j]):
                    end = j
                    break
            return i, end
    return None


def _edit_platform(lines: list[str], platform: str, add: list[str], drop: list[str]) -> list[str]:
    section = _section(lines)
    if section is None:
        raise ValueError("no top-level sources: list")
    start, end = section
    items = [(i, m) for i in range(start + 1, end) if (m := _ITEM_RE.match(lines[i]))]
    drop_keys = {d.casefold() for d in drop}

    def merged(current: list[str]) -> list[str]:
        kept = [t for t in current if t.casefold() not in drop_keys]
        known = {t.casefold() for t in kept}
        return kept + [a for a in add if a.casefold() not in known]

    for n, (i, m) in enumerate(items):
        if m.group(2) != platform:
            continue
        block_end = items[n + 1][0] if n + 1 < len(items) else end
        key_indent = m.group(1) + "  "
        for j in range(i + 1, block_end):
            t = _TENANTS_RE.match(lines[j])
            if not t:
                continue
            rest = t.group(2)
            if rest.startswith("["):
                close = rest.find("]")
                if close < 0:
                    raise ValueError(f"{platform} tenants list spans lines; edit it by hand")
                current = yaml.safe_load(rest[: close + 1]) or []
                lines[j] = f"{t.group(1)}tenants: [{', '.join(_scalar(x) for x in merged(current))}]{rest[close + 1:]}"
                return lines
            if rest and not rest.startswith("#"):
                raise ValueError(f"{platform} tenants is not a list")
            k = j + 1
            current_lines: list[int] = []
            while k < block_end and re.match(rf"^{re.escape(t.group(1))}\s+-\s+", lines[k]):
                current_lines.append(k)
                k += 1
            current = [yaml.safe_load(lines[x].split("-", 1)[1].split(" #")[0]) for x in current_lines]
            item_indent = re.match(r"^(\s*)-", lines[current_lines[0]]).group(1) if current_lines else t.group(1) + "  "
            new = [f"{item_indent}- {_scalar(x)}" for x in merged([str(c) for c in current])]
            return lines[: j + 1] + new + lines[k:]
        return lines[: i + 1] + [f"{key_indent}tenants: [{', '.join(_scalar(a) for a in add)}]"] + lines[i + 1:]

    if not add:
        return lines
    indent = items[0][1].group(1) if items else "  "
    insert_at = end
    while insert_at - 1 > start and not lines[insert_at - 1].strip():
        insert_at -= 1
    block = [f"{indent}- name: {platform}", f"{indent}  tenants: [{', '.join(_scalar(a) for a in add)}]"]
    return lines[:insert_at] + block + lines[insert_at:]


def apply(config_path: Path, added: dict[str, list[str]], removed: dict[str, list[str]]) -> None:
    """Write the board-list changes into ``config.yaml``; raise ValueError if unsafe."""
    if not added and not removed:
        return
    text = config_path.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    before = yaml.safe_load(text) or {}
    lines = text.splitlines()
    for platform in sorted(set(added) | set(removed)):
        lines = _edit_platform(lines, platform, added.get(platform, []), removed.get(platform, []))
    new_text = newline.join(lines) + newline

    after = yaml.safe_load(new_text) or {}
    expected = json.loads(json.dumps(before))
    blocks = expected.setdefault("sources", [])
    for platform in sorted(set(added) | set(removed)):
        targets = [b for b in blocks if b.get("name") == platform]
        if not targets:
            targets = [{"name": platform, "tenants": []}]
            blocks.append(targets[0])
        block = targets[0]
        drop = {d.casefold() for d in removed.get(platform, [])}
        tenants = [t for t in block.get("tenants") or [] if t.casefold() not in drop]
        known = {t.casefold() for t in tenants}
        block["tenants"] = tenants + [a for a in added.get(platform, []) if a.casefold() not in known]
    if after != expected:
        raise ValueError("edited config.yaml did not parse to the intended change; left unchanged")
    config_path.write_text(new_text, encoding="utf-8", newline="")
