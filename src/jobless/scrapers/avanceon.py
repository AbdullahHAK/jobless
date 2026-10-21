import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://avanceon.breezy.hr"
CAREERS_URL = f"{BASE_URL}/"
REQUEST_TIMEOUT_SECONDS = 10

# Breezy-hosted careers page, same pattern as Dubizzle/Strategic Systems
# International. Avanceon is a PSX-listed Pakistani industrial automation
# and systems-integration company hiring across Pakistan, Qatar, Saudi
# Arabia, and the UAE - every posting's location resolves to a single,
# literal city (no "%LABEL_MULTIPLE_LOCATIONS%" placeholder seen on this
# board, unlike some other Breezy-hosted companies), so postings are kept
# whenever the location string ends in ", PK" rather than matching a fixed
# city set - Avanceon posts across several real Pakistani cities (Lahore,
# Karachi, Sheikhupura seen so far), not just one or two. The page repeats
# every posting under a per-location grouping, same as Dubizzle, so
# entries are deduped by href. robots.txt only disallows static-asset
# paths and AhrefsBot specifically.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class AvanceonScraper(Scraper):
    company_name = "Avanceon"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("li.position"):
            location_el = item.select_one(".location span")
            location = location_el.get_text(strip=True) if location_el else None
            if location is None or not location.endswith(", PK"):
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
