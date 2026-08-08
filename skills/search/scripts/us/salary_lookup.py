#!/usr/bin/env python3
"""Look up base-salary stats for a company (+ optional role) from the local DOL index.

Deterministic filter + aggregate over salary_index.sqlite — same inputs, same output,
no network, no LLM. Build the index first with salary_index.py.

  --company "Acme"          required; matched on normalized employer key (suffix-insensitive)
  --role "backend engineer" optional substring filter on JOB_TITLE / SOC_TITLE
  --soc 15-1252             optional exact SOC-code filter (most precise)
  --json                    emit a JSON object instead of a text summary

Output: {low, median, high, n, wage_from_p25/p75, pw_level_mix, quarters, source,
confidence}. Wages are employer-committed BASE pay (no equity/bonus) — a lower bound.
"""
import argparse
import json
import sqlite3
import statistics
import sys
from collections import Counter

from salary_common import DB_PATH, norm_employer


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo = int(k)
    if lo == len(sorted_vals) - 1:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[lo + 1] - sorted_vals[lo]) * (k - lo)


def lookup(company, role=None, soc=None):
    if not DB_PATH.exists():
        sys.exit(f"index not found at {DB_PATH} — run salary_index.py first")
    key = norm_employer(company)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    # Exact normalized match first; fall back to substring if the exact key misses.
    where = ["employer_norm = ?"]
    params = [key]
    if soc:
        # Stored codes carry a detail suffix (15-1252.00, .03); match the base code too.
        where.append("(soc_code = ? OR soc_code LIKE ?)")
        params += [soc, f"{soc.split('.')[0]}.%"]
    if role:
        where.append("(LOWER(job_title) LIKE ? OR LOWER(soc_title) LIKE ?)")
        params += [f"%{role.lower()}%", f"%{role.lower()}%"]
    sql = f"SELECT * FROM filings WHERE {' AND '.join(where)}"
    rows = con.execute(sql, params).fetchall()
    if not rows:  # widen employer match to substring
        params[0] = f"%{key}%"
        rows = con.execute(sql.replace("employer_norm = ?", "employer_norm LIKE ?", 1), params).fetchall()
    con.close()

    if not rows:
        return {"company": company, "role": role, "soc": soc, "n": 0,
                "source": "dol_lca_base", "confidence": "none",
                "note": "no certified LCA filings matched"}

    wages = sorted(r["wage_from_annual"] for r in rows)
    levels = Counter(r["pw_level"] for r in rows if r["pw_level"])
    quarters = sorted({r["quarter"] for r in rows})
    sites = Counter(f'{r["city"]}, {r["state"]}' for r in rows if r["city"])
    matched = sorted({r["employer_name"] for r in rows})

    n = len(wages)
    low_lvl = sum(levels.get(l, 0) for l in ("1", "2", "I", "II"))
    confidence = "low" if n < 5 or (levels and low_lvl / sum(levels.values()) > 0.6) else \
                 "medium" if n < 25 else "high"
    return {
        "company": company,
        "matched_employers": matched[:5],
        "role": role, "soc": soc, "n": n,
        "low": round(min(wages)), "median": round(statistics.median(wages)), "high": round(max(wages)),
        "p25": round(percentile(wages, 0.25)), "p75": round(percentile(wages, 0.75)),
        "pw_level_mix": dict(levels.most_common()),
        "top_worksites": [s for s, _ in sites.most_common(5)],
        "quarters": quarters,
        "source": "dol_lca_base",
        "confidence": confidence,
        "note": "BASE salary floor from H-1B/E-3 filings; excludes equity/bonus — lower bound",
    }


def fmt(res):
    if res["n"] == 0:
        return f'{res["company"]}: no DOL LCA match ({res["note"]}).'
    k = lambda v: f"${v:,.0f}"  # ASCII-only output (Windows console is cp1252, mangles en/em dashes)
    lines = [
        f'{res["company"]}  (matched: {", ".join(res["matched_employers"])})',
        f'  base salary  median {k(res["median"])}   p25-p75 {k(res["p25"])}-{k(res["p75"])}   range {k(res["low"])}-{k(res["high"])}',
        f'  n={res["n"]} filings   quarters={", ".join(res["quarters"])}   confidence={res["confidence"]}',
        f'  PW level mix: {res["pw_level_mix"]}',
        f'  worksites: {", ".join(res["top_worksites"])}',
        f'  {res["note"].replace("—", "-")}',
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True)
    ap.add_argument("--role", default=None)
    ap.add_argument("--soc", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = lookup(a.company, a.role, a.soc)
    print(json.dumps(res, indent=2) if a.json else fmt(res))


if __name__ == "__main__":
    main()
