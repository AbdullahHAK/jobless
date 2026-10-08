import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://apply.workable.com/api/v1/widget/accounts/pakistan-single-window"
REQUEST_TIMEOUT_SECONDS = 10

# Workable's public widget API - same pattern as Prime System Solutions/
# Dubizzle/Creative Chaos/Inbox Business Technologies. Pakistan Single
# Window is the government-mandated trade-facilitation platform (customs,
# regulatory agencies, and traders in one system) - tagged "Information
# Technology and Services" on its own job postings, a real in-house tech
# team rather than a pure government office. All postings seen so far are
# Pakistan-only with distinct application_urls, but grouping by URL is
# kept for consistency/defensiveness with the other Workable-based
# scrapers in case that ever changes.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class PakistanSingleWindowScraper(Scraper):
    company_name = "Pakistan Single Window"

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
