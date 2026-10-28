import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://jobs.jobvite.com"
CAREERS_URL = f"{BASE_URL}/zones/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# Jobvite-hosted careers page for Zones LLC, a US-HQ'd IT solutions/managed-
# services company with a large Islamabad/Lahore delivery center (same
# "foreign company's PK offshore hub" profile as NetSol/Contour Software).
# Server-rendered HTML, grouped into department tables - each real posting
# is a <tr> with the title in 'td.jv-job-list-name a' and a single location
# string in 'td.jv-job-list-location'. Postings open in several countries
# at once collapse to a "N Locations" badge with no location names given
# anywhere on this page (the real list only exists on the job's own detail
# page) - those are skipped entirely rather than guessed at, same pattern
# as Strategic Systems International's unresolved-multi-location skip.
# jobs.jobvite.com has no robots.txt at all (404 -> unrestricted).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class ZonesScraper(Scraper):
    company_name = "Zones"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for name_cell in soup.select("td.jv-job-list-name"):
            row = name_cell.parent
            location_cell = row.select_one("td.jv-job-list-location") if row else None
            if location_cell is None:
                continue
            # The location text spans multiple source lines with real
            # whitespace between them ("Islamabad,\n  Pakistan"), unlike
            # most other scrapers' single-line location strings - collapse
            # it to one clean "Islamabad, Pakistan" rather than storing the
            # raw multi-line text verbatim.
            location = " ".join(location_cell.get_text(strip=True).split())
            if "pakistan" not in location.lower():
                continue

            link_el = name_cell.select_one("a[href]")
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
