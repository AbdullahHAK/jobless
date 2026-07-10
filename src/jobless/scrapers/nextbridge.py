import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://nextbridge.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# Nextbridge's careers page is a plain server-rendered WordPress page (their
# robots.txt only disallows /wp-admin/, and even explicitly Allows ClaudeBot)
# - every open role is already present in the initial HTML response as a
# table row inside '<div class="job-list" id="job-list"><table>', with the
# title+apply link in a '<td class="talent-acquisition-job-title"><a
# href="...">' cell and the location in the next plain '<td>'. No JS
# rendering, no ATS API, no pagination - one requests.get + BeautifulSoup
# parse is enough.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class NextbridgeScraper(Scraper):
    company_name = "Nextbridge"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        job_list = soup.find(id="job-list")
        if job_list is None:
            logger.warning("job-list container not found on %s", CAREERS_URL)
            return jobs

        for row in job_list.select("table tr"):
            title_cell = row.select_one("td.talent-acquisition-job-title a")
            if title_cell is None or not title_cell.get("href"):
                continue

            location_cell = title_cell.find_parent("td").find_next_sibling("td")
            location = location_cell.get_text(strip=True) if location_cell else "Not specified"

            jobs.append(
                Job(
                    title=title_cell.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=title_cell["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
