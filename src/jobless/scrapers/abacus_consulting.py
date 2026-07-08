import logging
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

# Abacus Consulting's careers page is hosted on the third-party "careers-page.com"
# ATS platform (https://abacus-consulting-3.careers-page.com/), linked to from
# their corporate site (https://abacus-global.com/). It's plain server-rendered
# HTML, not a JS SPA and not backed by any ATS with a documented public JSON
# API: every open role for the current page is already present in the initial
# HTML response as an '<a class="job-title-link" data-job-title="..."
# data-job-city="..." data-job-country="..." href="/jobs/{uuid}">' element, and
# listings are paginated across multiple pages ("Page X of Y" in a
# 'page-indicator' element) via a '?page=N' query string. So we page through
# with plain requests + BeautifulSoup - no API to reverse-engineer, no browser
# rendering needed.
BASE_URL = "https://abacus-consulting-3.careers-page.com/"
JOB_DETAIL_URL = "https://abacus-consulting-3.careers-page.com/jobs/{job_id}"
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_PAGES_SECONDS = 1

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}

PAGE_INDICATOR_RE = re.compile(r"Page\s+\d+\s+of\s+(\d+)", re.IGNORECASE)


@register
class AbacusConsultingScraper(Scraper):
    company_name = "Abacus Consulting"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        page_number = 1
        total_pages = 1

        while page_number <= total_pages:
            response = requests.get(
                BASE_URL,
                params={"page": page_number},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            if page_number == 1:
                indicator = soup.find(class_="page-indicator")
                if indicator is not None:
                    match = PAGE_INDICATOR_RE.search(indicator.get_text(" ", strip=True))
                    if match:
                        total_pages = int(match.group(1))

            for link in soup.find_all("a", class_="job-title-link"):
                job_id = link.get("data-job-id")
                title = (link.get("data-job-title") or link.get_text(strip=True)).strip()
                if not job_id or not title:
                    continue

                city = (link.get("data-job-city") or "").strip()
                country = (link.get("data-job-country") or "").strip()
                if city and country:
                    location = f"{city}, {country}"
                else:
                    location = city or country or "Not specified"

                jobs.append(
                    Job(
                        title=title,
                        company=self.company_name,
                        location=location,
                        apply_link=JOB_DETAIL_URL.format(job_id=job_id),
                        date_scraped=date.today(),
                    )
                )

            page_number += 1

            if page_number <= total_pages:
                time.sleep(DELAY_BETWEEN_PAGES_SECONDS)

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
