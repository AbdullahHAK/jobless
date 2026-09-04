import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://mindstormstudios.simplicant.com/"
REQUEST_TIMEOUT_SECONDS = 10

# The careers page (Simplicant-hosted) server-renders every opening twice -
# once in a "Featured Jobs" carousel and again under its department
# heading - both linking to the exact same job via the exact same href, so
# entries are deduped by that URL rather than double-counted. robots.txt is
# an empty file (no rules at all), so crawling is unrestricted.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class MindstormStudiosScraper(Scraper):
    company_name = "Mindstorm Studios"

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
