import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://apply.workable.com/api/v1/widget/accounts/remotebase"
REQUEST_TIMEOUT_SECONDS = 10

# Workable's public widget API - no auth needed. Remotebase hires in both
# Pakistan and the US; filtered to Pakistan-tagged postings only. Unlike
# Prime System Solutions, Remotebase's postings don't repeat per-city (each
# has its own unique application_url), so no grouping/merging is needed
# here - city just happens to be blank on every current PK posting.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class RemotebaseScraper(Scraper):
    company_name = "Remotebase"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("jobs", []):
            if item.get("country") != "Pakistan":
                continue

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company_name,
                    location=item.get("city") or "Not specified",
                    apply_link=item["application_url"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
