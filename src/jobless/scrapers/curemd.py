import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://curemd.wd1.myworkdayjobs.com/wday/cxs/curemd/CureMD/jobs"
CAREERS_BASE_URL = "https://curemd.wd1.myworkdayjobs.com/CureMD"
PAGE_SIZE = 20
REQUEST_TIMEOUT_SECONDS = 10

# CureMD's public careers page (curemd.com/career.asp) is Workday-hosted and
# renders client-side, but Workday exposes the same listings as a plain JSON
# POST endpoint used by its own frontend - no browser/JS needed. robots.txt
# (curemd.wd1.myworkdayjobs.com/robots.txt) only disallows /refreshFacet/;
# this /wday/cxs/.../jobs search endpoint isn't restricted. The endpoint
# paginates via limit/offset, but only the very first response reliably
# reports `total` (later pages return total=0, a Workday API quirk) - so
# pagination stops once a page returns fewer than PAGE_SIZE results instead
# of trusting `total`.
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
        offset = 0

        while True:
            response = requests.post(
                JOBS_API_URL,
                json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": ""},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            postings = response.json().get("jobPostings", [])

            for item in postings:
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

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
