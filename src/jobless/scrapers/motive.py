import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://boards-api.greenhouse.io/v1/boards/gomotive/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# Same Greenhouse public API pattern already used for Careem - no auth
# needed, robots.txt only disallows /embed/. Motive hires globally, so
# postings are kept only when "Pakistan" appears in the location string.
# One recurring posting, "Interested in joining our team?", is a generic
# talent-pool catch-all rather than a real opening (same pattern as
# Genetech's "Other Positions" and Bazaar's "Talent Pool" entries) and is
# excluded by title.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}
CATCH_ALL_TITLE = "Interested in joining our team?"


@register
class MotiveScraper(Scraper):
    company_name = "Motive"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("jobs", []):
            title = item["title"].strip()
            if title == CATCH_ALL_TITLE:
                continue

            location = (item.get("location") or {}).get("name") or ""
            if "Pakistan" not in location:
                continue

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    apply_link=item["absolute_url"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
