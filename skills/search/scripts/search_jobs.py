import argparse
import json
import sys

from jobspy import scrape_jobs


def main():
    p = argparse.ArgumentParser(description="JobSpy search pass")
    p.add_argument("--search-term", required=True)
    p.add_argument("--location", default="Remote")
    p.add_argument("--sites", default="linkedin,indeed",
                   help="comma list: linkedin,indeed,glassdoor,zip_recruiter,google,bayt,naukri")
    p.add_argument("--hours-old", type=int, default=72,
                   help="only postings from the last N hours (newest-first policy)")
    p.add_argument("--results", type=int, default=25, help="per-site result cap")
    p.add_argument("--remote", action="store_true")
    p.add_argument("--country-indeed", default=None,
                   help="required for indeed/glassdoor, e.g. 'canada', 'germany'")
    p.add_argument("--full-descriptions", action="store_true",
                   help="fetch full JDs (much slower; more rate-limit exposure)")
    p.add_argument("--out", default=None, help="write results as JSON lines to this path")
    args = p.parse_args()

    kwargs = dict(
        site_name=args.sites.split(","),
        search_term=args.search_term,
        location=args.location,
        results_wanted=args.results,
        hours_old=args.hours_old,
        is_remote=args.remote,
        linkedin_fetch_description=args.full_descriptions,
    )
    if args.country_indeed:
        kwargs["country_indeed"] = args.country_indeed

    jobs = scrape_jobs(**kwargs)

    cols = ["site", "title", "company", "location", "date_posted",
            "min_amount", "max_amount", "currency", "job_url"]
    cols = [c for c in cols if c in jobs.columns]
    jobs = jobs.sort_values("date_posted", ascending=False)

    if args.out:
        jobs[cols].to_json(args.out, orient="records", lines=True,
                           date_format="iso", force_ascii=False)
        print(f"{len(jobs)} jobs -> {args.out}")
    else:
        jobs[cols].to_json(sys.stdout, orient="records", lines=True,
                           date_format="iso", force_ascii=False)


if __name__ == "__main__":
    main()
