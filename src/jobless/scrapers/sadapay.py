import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://sadapay.pk"
CAREERS_URL = f"{BASE_URL}/careers"
REQUEST_TIMEOUT_SECONDS = 10

# Webflow-hosted careers page (a Webflow CMS collection, server-rendered -
# no JS needed). robots.txt is wide open (Disallow: with no path). Each
# posting's location is already a single, pre-joined string ("Karachi,
# Lahore, Islamabad") straight from the page, so no per-city grouping is
# needed the way the Workable-based scrapers require.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class SadaPayScraper(Scraper):
    company_name = "SadaPay"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("a.job-wrap[href]"):
            title_el = item.select_one(".job-heading")
            if title_el is None:
                continue

            location_el = item.select_one(".job-location p")
            location = location_el.get_text(strip=True) if location_el else "Not specified"

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + item["href"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
