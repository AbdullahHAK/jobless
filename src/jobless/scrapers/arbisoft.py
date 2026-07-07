import logging
import time
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://arbisoft.hirestream.io/api/v1/jobs/published-jobs/"
JOB_DETAIL_URL = "https://arbisoft.hirestream.io/job/view-job/{uuid}/"
PAGE_SIZE = 25
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_PAGES_SECONDS = 1

# Arbisoft's careers page (a React SPA) loads listings from this same public,
# unauthenticated JSON endpoint - found by inspecting the page's network
# requests, not by reverse-engineering anything private. It returns the exact
# data an anonymous visitor's browser already receives, so we call it
# directly instead of driving a full browser just to re-render it.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class ArbisoftScraper(Scraper):
    company_name = "Arbisoft"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        url: str | None = JOBS_API_URL
        params: dict | None = {
            "timezone": "Asia/Karachi",
            "offset": 0,
            "limit": PAGE_SIZE,
            "order": "featured",
        }

        while url:
            response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()

            for item in payload["results"]:
                jobs.append(
                    Job(
                        title=item["title"],
                        company=self.company_name,
                        location=item["location"],
                        apply_link=JOB_DETAIL_URL.format(uuid=item["uuid"]),
                        date_scraped=date.today(),
                    )
                )

            url = payload.get("next")
            params = None  # 'next' is already a full URL with its own query string

            if url:
                time.sleep(DELAY_BETWEEN_PAGES_SECONDS)

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
