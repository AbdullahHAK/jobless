import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://careers.jobscore.com"
CAREERS_URL = f"{BASE_URL}/careers/convo"
REQUEST_TIMEOUT_SECONDS = 10

# JobScore-hosted careers page for Convo's Islamabad engineering office (the
# US-HQ'd workplace-collaboration platform - same "foreign company, real PK
# engineering office" profile as Motive/Securiti). Server-rendered HTML, no
# API: each posting is a '.js-job-list-item' row with the title in
# '.js-job-title a' (relative href) and location in '.js-job-location'.
# This specific board currently only lists the Islamabad office's openings,
# but the location text is still checked defensively in case a non-PK role
# ever gets added here. robots.txt only disallows /apply_flow/.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class ConvoScraper(Scraper):
    company_name = "Convo"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select(".js-job-list-item"):
            location_el = item.select_one(".js-job-location")
            location = location_el.get_text(strip=True) if location_el else None
            if location is None or "pakistan" not in location.lower():
                continue

            link_el = item.select_one(".js-job-title a[href]")
            if link_el is None:
                continue

            jobs.append(
                Job(
                    title=link_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + link_el["href"],
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
