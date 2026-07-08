import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.venturedive.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# VentureDive's careers page embeds a JazzHR/"Resumator" job-board widget
# (hosted at venturedive.applytojob.com) directly into the server-rendered
# HTML: the full <div id="resumator-job-listings"> table - every open role,
# its department, its location and its "Apply" link - is already present in
# the plain HTML response, with no client-side rendering needed to see it.
# robots.txt on both venturedive.com and venturedive.applytojob.com allow
# fetching these paths for a general user agent, and the listing (and each
# job's own apply page) is publicly viewable with no login. So one
# requests.get + BeautifulSoup parse of the careers page is enough - no API
# to reverse-engineer, no browser rendering needed, and no per-job requests.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class VentureDiveScraper(Scraper):
    company_name = "VentureDive"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        listings = soup.find(id="resumator-job-listings")
        if listings is None:
            logger.warning("resumator-job-listings container not found on %s", CAREERS_URL)
            return jobs

        for row in listings.select("tr.resumator-table-row-even, tr.resumator-table-row-odd"):
            title_el = row.select_one("a.resumator-job-title-link")
            location_el = row.select_one("td.resumator-job-location-column")
            if title_el is None or not title_el.get("href"):
                continue

            location = location_el.get_text(strip=True) if location_el else "Not specified"

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=title_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
