import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://pakeventures.simplicant.com/"
REQUEST_TIMEOUT_SECONDS = 10

# Same Simplicant-hosted pattern as Mindstorm Studios: the careers page
# server-renders every opening as an <a class="list-group-item">, with
# title/location inline. Some postings appear more than once across the
# page's featured/department sections, so entries are deduped by href.
# robots.txt is an empty file (no rules at all).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class PakWheelsScraper(Scraper):
    company_name = "PakWheels"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for link_el in soup.select("a.list-group-item[href]"):
            href = link_el["href"].strip()
            if "/jobs/" not in href:
                continue
            if href.startswith("//"):
                href = "https:" + href

            if href in seen_links:
                continue
            seen_links.add(href)

            title_el = link_el.select_one(".job-title")
            if title_el is None:
                continue

            location_el = link_el.select_one(".job-subtitle")

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location_el.get_text(strip=True) if location_el else "Not specified",
                    apply_link=href,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
