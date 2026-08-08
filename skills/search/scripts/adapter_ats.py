#!/usr/bin/env python3
"""ATS JSON adapter — pulls postings straight from company ATS public APIs.

Reads the `ats` registry in .agents/config/sources.json, fetches every row
marked `live` from its ATS's public JSON endpoint (no scraping, no login),
normalizes to the JobSpy field shape, applies the config's discipline + geo
filters, and writes JSON lines.

Same CLI contract as the JobSpy template so the search subagent runs it alongside:
  --search-term  substring filter on title (optional)
  --location     unused here (registry + per-posting country drives geo); accepted for parity
  --hours-old    drop postings older than N hours where a real date is available
  --results      cap emitted rows
  --out          output path for JSON lines (default: stdout)
  --config       registries + filters (default: .agents/config/sources.json)

Paths default relative to the CWD (run from the data-repo root).
"""
import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

from adapter_common import load_config, filters, live_rows, discipline_ok, is_us_ca, iso_date

UA = {"User-Agent": "job-search-adapter/1.0"}


def fetch(url, data=None, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="POST" if data else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(data).encode()
    with urllib.request.urlopen(req, data=data, timeout=30) as r:
        return json.loads(r.read())


def rec(site, title, company, location, date_posted, url, mn=None, mx=None, cur=None, dept=""):
    return {"site": site, "title": title, "company": company, "location": location,
            "date_posted": date_posted, "min_amount": mn, "max_amount": mx,
            "currency": cur, "job_url": url, "department": dept}


# --- per-ATS pulls ---------------------------------------------------------
def pull_greenhouse(row, term):
    # No server-side filter; ?content=true adds departments per job for the discipline gate.
    d = fetch(f"https://boards-api.greenhouse.io/v1/boards/{row['slug']}/jobs?content=true")
    for j in d.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        dept = ", ".join(x.get("name", "") for x in j.get("departments", []))
        yield rec("greenhouse", j.get("title", ""), row["company"], loc,
                  iso_date(j.get("updated_at")), j.get("absolute_url", ""), dept=dept)


def _ashby_salary(j):
    """Pull min/max/currency from a compensation Salary component if present."""
    for tier in j.get("compensation", {}).get("compensationTiers", []) or []:
        for c in tier.get("components", []) or []:
            if "salary" in (c.get("compensationType") or "").lower() and c.get("minValue"):
                return c.get("minValue"), c.get("maxValue"), c.get("currencyCode")
    return None, None, None


def pull_ashby(row, term):
    # Ashby has no server-side filter, but includeCompensation adds salary.
    d = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{row['slug']}?includeCompensation=true")
    for j in d.get("jobs", []):
        if not j.get("isListed", True):
            continue
        # collect all location strings incl. structured secondary countries
        locs = [j.get("location", "")]
        for s in j.get("secondaryLocations", []):
            addr = ((s.get("address") or {}).get("postalAddress") or {})
            locs.append(", ".join(filter(None, [addr.get("addressLocality"), addr.get("addressCountry")])) or s.get("location", ""))
        loc = " | ".join(filter(None, locs))
        mn, mx, cur = _ashby_salary(j)
        dept = " / ".join(filter(None, [j.get("department", ""), j.get("team", "")]))
        yield rec("ashby", j.get("title", ""), row["company"], loc,
                  iso_date(j.get("publishedAt")), j.get("jobUrl") or j.get("applyUrl", ""),
                  mn, mx, cur, dept)


def pull_lever(row, term):
    # Lever location/team filters are exact-match & case-sensitive (fragile) — filter client-side.
    d = fetch(f"https://api.lever.co/v0/postings/{row['slug']}?mode=json")
    for j in d:
        cats = j.get("categories") or {}
        loc = cats.get("location", "")
        dept = " / ".join(filter(None, [cats.get("department", ""), cats.get("team", "")]))
        created = j.get("createdAt")
        date = datetime.fromtimestamp(created / 1000, timezone.utc).date().isoformat() if created else None
        yield rec("lever", j.get("text", ""), row["company"], loc, date, j.get("hostedUrl", ""), dept=dept)


def pull_workday(row, term):
    # Workday filters server-side via searchText (keyword). No machine date, so no hours-old.
    wd, site = [p.strip() for p in row["extra"].split("/", 1)]  # extra = "<wdN> / <SitePath>"
    base = f"https://{row['slug']}.{wd}.myworkdayjobs.com"
    offset = 0
    while offset < 500:  # backstop; results cap trims downstream
        d = fetch(f"{base}/wday/cxs/{row['slug']}/{site}/jobs",
                  {"limit": 20, "offset": offset, "searchText": term})
        posts = d.get("jobPostings", [])
        if not posts:
            break
        for j in posts:
            url = f"{base}/en-US/{site}{j.get('externalPath', '')}"
            yield rec("workday", j.get("title", ""), row["company"],
                      j.get("locationsText", ""), None, url)
        offset += 20


def pull_eightfold(row, term):
    # Eightfold apply-v2: query AND location filter server-side. slug = microsite domain
    # (e.g. netflix.com), extra = the board host (e.g. explore.jobs.netflix.net). Needs Referer.
    base = f"https://{row['extra']}"
    hdr = {"Accept": "application/json", "Referer": f"{base}/careers"}
    q = urllib.parse.urlencode({"domain": row["slug"], "query": term, "location": "", "num": 50})
    start = 0
    while start < 500:  # backstop; results cap trims downstream
        d = fetch(f"{base}/api/apply/v2/jobs?{q}&start={start}", headers=hdr)
        posts = d.get("positions", [])
        if not posts:
            break
        for j in posts:
            t = j.get("t_create")
            date = datetime.fromtimestamp(t, timezone.utc).date().isoformat() if t else None
            yield rec("eightfold", j.get("name", ""), row["company"], j.get("location", ""),
                      date, j.get("canonicalPositionUrl", ""), dept=j.get("department", ""))
        if start + 50 >= d.get("count", 0):
            break
        start += 50


PULLERS = {"greenhouse": pull_greenhouse, "ashby": pull_ashby, "lever": pull_lever,
           "workday": pull_workday, "eightfold": pull_eightfold}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search-term", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--hours-old", type=int, default=0)
    ap.add_argument("--results", type=int, default=0)
    ap.add_argument("--out", default="")
    ap.add_argument("--config", default=".agents/config/sources.json")
    a = ap.parse_args()

    cfg = load_config(a.config)
    disc, geo = filters(cfg)
    term = a.search_term.lower()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=a.hours_old)).date().isoformat() if a.hours_old else None
    out = []
    for row in live_rows(cfg, "ats"):
        try:
            for r in PULLERS[row["ats"]](row, term):
                if not discipline_ok(f"{r.get('department', '')} {r['title']}", disc):
                    continue
                if term and term not in r["title"].lower():
                    continue
                if not is_us_ca(r["location"], geo):
                    continue
                if cutoff and r["date_posted"] and r["date_posted"] < cutoff:
                    continue
                out.append(r)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as e:
            # per boards.md: an adapter source that errors is noted and skipped, never fatal
            print(f"WARN {row['company']} ({row['ats']}): {e}", file=sys.stderr)

    if a.results:
        out = out[: a.results]
    payload = "\n".join(json.dumps(r) for r in out)
    if a.out:
        Path(a.out).write_text(payload, encoding="utf-8")
        print(f"wrote {len(out)} rows -> {a.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
