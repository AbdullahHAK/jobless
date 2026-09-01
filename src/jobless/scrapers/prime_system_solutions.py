import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://apply.workable.com/api/v1/widget/accounts/prime-system"
REQUEST_TIMEOUT_SECONDS = 10

# Workable's public widget API - no auth needed, the same endpoint every
# company running a hosted Workable board exposes. Prime System Solutions
# hires across Pakistan, South Africa, and the Philippines; a single role
# open in multiple Pakistani cities comes back as one row per city, all
# sharing the same application_url - so entries are grouped by that URL and
# their cities merged into one location string, rather than letting later
# cities silently overwrite earlier ones via the DB's upsert-by-apply_link.
# Non-Pakistan rows are dropped before grouping, so a role also open
# elsewhere (which gets its own, different application_url per region)
# never leaks a foreign city into a Pakistan posting's location.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class PrimeSystemSolutionsScraper(Scraper):
    company_name = "Prime System Solutions"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        grouped: dict[str, dict] = {}
        for item in payload.get("jobs", []):
            if item.get("country") != "Pakistan":
                continue

            url = item["application_url"]
            entry = grouped.setdefault(url, {"title": item["title"], "cities": set()})
            city = item.get("city")
            if city:
                entry["cities"].add(city)

        jobs: list[Job] = []
        for url, data in grouped.items():
            jobs.append(
                Job(
                    title=data["title"],
                    company=self.company_name,
                    location=", ".join(sorted(data["cities"])) or "Not specified",
                    apply_link=url,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
