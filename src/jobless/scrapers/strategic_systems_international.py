import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://strategic-systems-international.breezy.hr"
CAREERS_URL = f"{BASE_URL}/"
REQUEST_TIMEOUT_SECONDS = 10

# Breezy-hosted careers page. This company hires globally (Argentina,
# Brazil, Colombia, Dubai, Lahore, Mexico, Uruguay); a role open in
# several countries at once renders its location as an unresolved
# "%LABEL_MULTIPLE_LOCATIONS%" template placeholder rather than naming
# them, so those are skipped entirely rather than guessed at - only
# postings whose location resolves to the literal, single "Lahore, PK"
# are kept. robots.txt only disallows a few static-asset paths and
# AhrefsBot specifically.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
TARGET_LOCATION = "Lahore, PK"


@register
class StrategicSystemsInternationalScraper(Scraper):
    company_name = "Strategic Systems International"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("li.position"):
            location_el = item.select_one(".location span")
            if location_el is None or location_el.get_text(strip=True) != TARGET_LOCATION:
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
                    location=TARGET_LOCATION,
                    apply_link=BASE_URL + href,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
