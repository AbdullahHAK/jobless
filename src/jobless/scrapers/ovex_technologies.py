import logging
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.ovextech.com/career"
REQUEST_TIMEOUT_SECONDS = 10

# Ovex's careers page (note: singular "/career", "/careers" 404s) server-
# renders each opening as a <div class="box"> under the "Open Positions"
# heading - title in <h4 class="head">, location in a
# <p class="desc"><b>Location: ...</b></p> line, apply link in
# <a class="more-btn">. robots.txt has no User-agent/Disallow rules at all
# (only opt-in AI content-signal preferences), so crawling is unrestricted.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
LOCATION_PREFIX = re.compile(r"^location:\s*", re.IGNORECASE)


@register
class OvexTechnologiesScraper(Scraper):
    company_name = "Ovex Technologies"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for box in soup.select("div.box"):
            title_el = box.select_one("h4.head")
            apply_el = box.select_one("a.more-btn")
            if title_el is None or apply_el is None or not apply_el.get("href"):
                continue

            location = "Not specified"
            for desc in box.select("p.desc"):
                bold = desc.find("b")
                if bold and "location" in bold.get_text(strip=True).lower():
                    location = LOCATION_PREFIX.sub("", bold.get_text(strip=True)).strip()
                    break

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=apply_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
