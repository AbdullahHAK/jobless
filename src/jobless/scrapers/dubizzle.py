import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://dubizzlelabs.breezy.hr"
CAREERS_URL = f"{BASE_URL}/"
REQUEST_TIMEOUT_SECONDS = 10

# Dubizzle's main domain (careers.dubizzle.com) doesn't resolve - their
# Pakistan engineering org ("Dubizzle Labs", ~400 people across Lahore and
# Karachi per their own careers copy) hires through this separate Breezy-
# hosted board instead. Same Breezy quirk as Strategic Systems
# International: a role open in multiple locations at once renders as an
# unresolved "%LABEL_MULTIPLE_LOCATIONS%" placeholder rather than naming
# them, so those are skipped - only postings resolving to a single literal
# Pakistan city are kept. robots.txt only disallows static-asset paths and
# AhrefsBot specifically.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
TARGET_LOCATIONS = {"Lahore, PK", "Karachi, PK"}


@register
class DubizzleScraper(Scraper):
    company_name = "Dubizzle"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("li.position"):
            location_el = item.select_one(".location span")
            location = location_el.get_text(strip=True) if location_el else None
            if location not in TARGET_LOCATIONS:
                continue

            link_el = item.select_one(".position-details a[href]")
            title_el = link_el.find("h2") if link_el else None
            if link_el is None or title_el is None:
                continue

            href = link_el["href"]
            if href in seen_links:
                continue
            seen_links.add(href)

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + href,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
