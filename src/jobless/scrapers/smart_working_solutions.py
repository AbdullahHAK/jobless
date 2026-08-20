import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://api.lever.co/v0/postings/smart-working-solutions?mode=json"
REQUEST_TIMEOUT_SECONDS = 10

# Lever's public postings API - no auth needed, the same endpoint every
# company running a hosted Lever board (jobs.lever.co/<company>) exposes.
# This board recruits globally, not only for Pakistan, so a posting is kept
# only when "Pakistan" appears in the primary location or any of the listed
# locations - some postings are tagged with a single PK city (e.g. "Lahore")
# as the primary location, with "Pakistan" only appearing inside another
# entry in allLocations (e.g. "Hyderabad, Pakistan").
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


def _is_pakistan(categories: dict) -> bool:
    location = categories.get("location") or ""
    all_locations = categories.get("allLocations") or []
    return "Pakistan" in location or any("Pakistan" in loc for loc in all_locations)


@register
class SmartWorkingSolutionsScraper(Scraper):
    company_name = "Smart Working Solutions"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload:
            categories = item.get("categories", {})
            if not _is_pakistan(categories):
                continue

            jobs.append(
                Job(
                    title=item["text"],
                    company=self.company_name,
                    location=categories.get("location") or "Not specified",
                    apply_link=item["hostedUrl"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
