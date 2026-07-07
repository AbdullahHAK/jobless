import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

# Devsinc's official careers page (https://www.devsinc.com/career) links out
# entirely to a Workable-hosted careers site
# (https://apply.workable.com/devsinc-17/) for job listings and applications.
# That hosted page renders its listings from Workable's public, unauthenticated
# "widget" JSON endpoint - found by inspecting the page's network requests. It
# returns the full, unpaginated list of currently published jobs exactly as an
# anonymous visitor's browser receives it, so we call it directly instead of
# driving a full browser just to re-render it.
JOBS_WIDGET_URL = "https://apply.workable.com/api/v1/widget/accounts/devsinc-17"
REQUEST_TIMEOUT_SECONDS = 10

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class DevsincScraper(Scraper):
    company_name = "Devsinc"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(JOBS_WIDGET_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        for item in payload["jobs"]:
            city = (item.get("city") or "").strip()
            country = (item.get("country") or "").strip()
            if city and country:
                location = f"{city}, {country}"
            else:
                location = city or country or "Not specified"

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company_name,
                    location=location,
                    apply_link=item["url"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
