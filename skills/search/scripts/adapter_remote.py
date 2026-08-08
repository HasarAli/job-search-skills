#!/usr/bin/env python3
"""Remote-board adapter — pulls postings from fully-remote job boards' public feeds.

Reads the `remote_feeds` registry in .agents/config/sources.json, fetches every
row marked `live` from its feed/API (Himalayas JSON, Remote OK + WWR RSS),
normalizes to the JobSpy field shape, applies the config's discipline filter, and
keeps remote-first geo: worldwide + US + CA, dropping only roles explicitly
restricted to a non-North-America region.

Same CLI contract as the JobSpy template:
  --search-term  substring filter on title (optional)
  --location     accepted for contract parity (geo is driven by the remote rule)
  --hours-old    drop postings older than N hours (all sources carry real dates)
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
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone, timedelta
from pathlib import Path

from adapter_common import load_config, filters, live_rows, discipline_ok, remote_geo_ok

UA = {"User-Agent": "Mozilla/5.0 (job-search-adapter/1.0)"}


def fetch(url):
    req = urllib.request.Request(url, headers=dict(UA))
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def rec(site, title, company, location, date_posted, url,
        mn=None, mx=None, cur=None):
    return {"site": site, "title": title, "company": company, "location": location,
            "date_posted": date_posted, "min_amount": mn, "max_amount": mx,
            "currency": cur, "job_url": url}


# --- per-source parsers ----------------------------------------------------
def parse_himalayas(url, term):
    # /jobs/api/search filters server-side: q=keyword, country=<name>, worldwide=true, sort=recent.
    # Union three geo scopes (US, CA, worldwide) so a Canada-based search sees all it can take.
    seen = set()
    for key, val in (("country", "United States"), ("country", "Canada"), ("worldwide", "true")):
        params = {key: val, "sort": "recent"}
        if term:
            params["q"] = term
        d = json.loads(fetch(f"{url}?{urllib.parse.urlencode(params)}"))
        for j in d.get("jobs", []):
            guid = j.get("guid") or j.get("applicationLink")
            if guid in seen:
                continue
            seen.add(guid)
            restr = ", ".join(j.get("locationRestrictions") or []) or "Anywhere"
            pub = j.get("pubDate")
            date = datetime.fromtimestamp(int(pub), timezone.utc).date().isoformat() if pub else None
            yield rec("himalayas", j.get("title", ""), j.get("companyName", ""), restr, date,
                      j.get("applicationLink") or f"https://himalayas.app/companies/{j.get('companySlug','')}",
                      j.get("minSalary"), j.get("maxSalary"), j.get("currency"))


def _rss_items(url):
    return ET.fromstring(fetch(url)).findall(".//item")


def parse_remoteok(url, term):
    for it in _rss_items(url):
        g = {c.tag: (c.text or "").strip() for c in it}
        date = None
        if g.get("pubDate"):
            try:
                date = datetime.fromisoformat(g["pubDate"].replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
        yield rec("remoteok", g.get("title", ""), g.get("company", ""),
                  g.get("location", ""), date, g.get("link", ""))


def parse_wwr(url, term):
    for it in _rss_items(url):
        g = {c.tag: (c.text or "").strip() for c in it}
        title = g.get("title", "")
        company, _, role = title.partition(":")  # "Company: Role"
        date = None
        if g.get("pubDate"):
            try:
                date = parsedate_to_datetime(g["pubDate"]).date().isoformat()
            except (TypeError, ValueError):
                pass
        yield rec("wwr", (role or title).strip(), company.strip(),
                  g.get("region", ""), date, g.get("link", ""))


PARSERS = {"himalayas": parse_himalayas, "remoteok": parse_remoteok, "wwr": parse_wwr}


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
    for row in live_rows(cfg, "remote_feeds"):
        try:
            for r in PARSERS[row["kind"]](row["url"], term):
                if not discipline_ok(r["title"], disc):
                    continue
                if term and term not in r["title"].lower():
                    continue
                if not remote_geo_ok(r["location"], geo):
                    continue
                if cutoff and r["date_posted"] and r["date_posted"] < cutoff:
                    continue
                out.append(r)
        except (urllib.error.URLError, urllib.error.HTTPError, ET.ParseError, ValueError, KeyError) as e:
            print(f"WARN {row['source']} ({row['kind']}): {e}", file=sys.stderr)

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
