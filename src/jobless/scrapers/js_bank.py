import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.jsbl.com/job-openings/"
REQUEST_TIMEOUT_SECONDS = 10

# JS Bank's job openings page (built on the "AWSM Job Openings" WordPress
# plugin) server-renders every posting, past and present, as a
# .awsm-job-listing-item - but the plugin itself tags expired postings with
# an extra "awsm-job-expired-item" class rather than removing them, so
# those are filtered out here rather than trusted at face value (confirmed
# by inspection: half the listed postings on this page carry that class).
# robots.txt only disallows /wp-admin/.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
EXPIRED_CLASS = "awsm-job-expired-item"


@register
class JSBankScraper(Scraper):
    company_name = "JS Bank"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("div.awsm-job-listing-item"):
            if EXPIRED_CLASS in item.get("class", []):
                continue

            link_el = item.select_one("a.awsm-job-item")
            title_el = item.select_one(".awsm-job-post-title")
            if link_el is None or title_el is None or not link_el.get("href"):
                continue

            location_el = item.select_one(".awsm-job-specification-job-location")

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location_el.get_text(strip=True) if location_el else "Not specified",
                    apply_link=link_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
