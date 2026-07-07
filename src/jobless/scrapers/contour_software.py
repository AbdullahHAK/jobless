import logging
import time
from datetime import date
from urllib.parse import quote

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

# Contour Software's careers page (https://contour-software.com/jobs/) is a
# WordPress page whose job list is populated client-side by a fetch() call to
# this same-origin PHP endpoint (found by reading the page's inline <script>,
# not by reverse-engineering anything private). It is a thin, unauthenticated
# proxy in front of the company's actual Workday tenant
# (talentmanagementsolution.wd3.myworkdayjobs.com/ContourSoftware-Careers) -
# calling it directly returns the exact JSON an anonymous visitor's browser
# already receives, so we use it instead of driving a full browser.
#
# Each listing's "View Job" button just opens
# https://contour-software.com/job-detail/?jobPath=<path>&jobTitle=<title> on
# Contour's own site (which in turn fetches the single-job detail from the
# same proxy), so that same-origin URL is used as apply_link. This avoids an
# extra per-job request and avoids sending any request to the third-party
# Workday tenant at all.
JOBS_API_URL = "https://contour-software.com/service.php?slug=jobs"
JOB_DETAIL_PAGE_URL = "https://contour-software.com/job-detail/?jobPath={job_path}&jobTitle={job_title}"
PAGE_SIZE = 12  # matches the careers page's own recordsPerPage
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_PAGES_SECONDS = 1

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


@register
class ContourSoftwareScraper(Scraper):
    company_name = "Contour Software"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        offset = 0

        while True:
            payload = {
                "appliedFacets": {},
                "limit": PAGE_SIZE,
                "offset": offset,
                "searchText": "",
            }
            response = requests.post(
                JOBS_API_URL, json=payload, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()

            postings = data.get("jobPostings", [])
            if not postings:
                break

            for item in postings:
                job_path = item["externalPath"]
                jobs.append(
                    Job(
                        title=item["title"],
                        company=self.company_name,
                        location=item.get("locationsText", "Pakistan"),
                        apply_link=JOB_DETAIL_PAGE_URL.format(
                            job_path=quote(job_path, safe=""),
                            job_title=quote(item["title"], safe=""),
                        ),
                        date_scraped=date.today(),
                    )
                )

            offset += len(postings)
            total = data.get("total", 0)
            if offset >= total:
                break

            time.sleep(DELAY_BETWEEN_PAGES_SECONDS)

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
