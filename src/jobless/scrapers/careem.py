import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://boards-api.greenhouse.io/v1/boards/careem/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# Greenhouse's public, documented job-board API - no auth needed, the same
# endpoint every company running a hosted Greenhouse board exposes.
# robots.txt only disallows /embed/, unrelated to this API path. Careem
# hires globally, not only for Pakistan, so a posting is kept only when
# "Pakistan" appears in its location string - which can list several
# offices at once, e.g. "Amman, Jordan; Islamabad, Pakistan; Karachi,
# Pakistan; Lahore, Pakistan" for a single role open across all of them.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class CareemScraper(Scraper):
    company_name = "Careem"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("jobs", []):
            location = (item.get("location") or {}).get("name") or ""
            if "Pakistan" not in location:
                continue

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company_name,
                    location=location,
                    apply_link=item["absolute_url"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
