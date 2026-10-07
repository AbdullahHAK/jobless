import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://curemd.wd1.myworkdayjobs.com/wday/cxs/curemd/CureMD/jobs"
CAREERS_BASE_URL = "https://curemd.wd1.myworkdayjobs.com/CureMD"
PAGE_SIZE = 20
# A generous but bounded cap, covering ~500 postings at PAGE_SIZE=20 (CureMD
# currently has ~40) - a pure safety net, see the real incident below.
MAX_PAGES = 25
REQUEST_TIMEOUT_SECONDS = 10

# CureMD's public careers page (curemd.com/career.asp) is Workday-hosted and
# renders client-side, but Workday exposes the same listings as a plain JSON
# POST endpoint used by its own frontend - no browser/JS needed. robots.txt
# (curemd.wd1.myworkdayjobs.com/robots.txt) only disallows /refreshFacet/;
# this /wday/cxs/.../jobs search endpoint isn't restricted.
#
# Real incident (2026-10-07): pagination originally stopped once a page
# returned fewer than PAGE_SIZE results, trusting that the last real page
# would come back short. It doesn't always - once `offset` passes the true
# end of results, this endpoint can keep re-returning a full, repeated page
# forever instead of ever returning fewer than PAGE_SIZE (`total` is also
# unreliable on later pages, a known quirk). That combination turned the
# scraper into an infinite loop and hung a live CI run for 15 minutes
# before GitHub Actions force-killed the job. Fixed by stopping as soon as
# a page contributes zero postings not already seen - the one signal that
# stayed correct in the incident - plus a hard MAX_PAGES cap below as a
# backstop against any other pagination failure mode.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


@register
class CureMDScraper(Scraper):
    company_name = "CureMD"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_paths: set[str] = set()
        offset = 0

        for _ in range(MAX_PAGES):
            response = requests.post(
                JOBS_API_URL,
                json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": ""},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            postings = response.json().get("jobPostings", [])
            if not postings:
                break

            new_postings = [item for item in postings if item["externalPath"] not in seen_paths]
            if not new_postings:
                break

            for item in new_postings:
                seen_paths.add(item["externalPath"])
                jobs.append(
                    Job(
                        title=item["title"],
                        company=self.company_name,
                        location=item.get("locationsText") or "Not specified",
                        apply_link=CAREERS_BASE_URL + item["externalPath"],
                        date_scraped=date.today(),
                    )
                )

            if len(postings) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        else:
            logger.warning(
                "CureMD pagination hit the %d-page safety cap - results may be incomplete", MAX_PAGES
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
