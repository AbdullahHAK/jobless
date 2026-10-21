import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://api.lever.co/v0/postings/educative?mode=json"
REQUEST_TIMEOUT_SECONDS = 10

# Lever's public postings API - same pattern as Smart Working Solutions,
# but simpler: each posting here carries its own top-level "country" ISO
# code (confirmed "PK" for the Lahore/Islamabad roles, "US" for the one
# Bellevue, WA role), which is more reliable than matching "Pakistan" as a
# substring of the location string - that substring never actually
# appears here since locations are just bare city names ("Lahore"). Worth
# checking for this field on any future Lever-based scraper before
# falling back to substring matching.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class EducativeScraper(Scraper):
    company_name = "Educative"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload:
            if item.get("country") != "PK":
                continue

            location = (item.get("categories") or {}).get("location") or "Not specified"

            jobs.append(
                Job(
                    title=item["text"],
                    company=self.company_name,
                    location=location,
                    apply_link=item["hostedUrl"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
