import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://boards-api.greenhouse.io/v1/boards/joblogic/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# Same Greenhouse public API pattern already used for Careem/Motive - no
# auth needed, robots.txt only disallows /embed/. Joblogic is a UK
# (Birmingham-headquartered) field-service-management SaaS company with a
# real, substantial Lahore engineering office - postings are kept only
# when "Pakistan" appears in the location string, same filter as Motive.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class JoblogicScraper(Scraper):
    company_name = "Joblogic"

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
                    title=item["title"].strip(),
                    company=self.company_name,
                    location=location,
                    apply_link=item["absolute_url"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
