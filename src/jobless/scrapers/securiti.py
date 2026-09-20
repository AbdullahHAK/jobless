import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://careers.veeam.com"
PAKISTAN_URL = f"{BASE_URL}/location/pakistan-jobs/22681/1168579/2"
REQUEST_TIMEOUT_SECONDS = 10

# Securiti's Pakistan hiring is posted on Veeam's careers portal (Veeam
# acquired Securiti; every Pakistan opening carries a "Securiti AI"
# category label). The whole portal uses one org id (22681), confirmed via
# its public sitemap, which lists exactly the same Pakistan jobs as this
# page. robots.txt only disallows /search-jobs/ - and that path also hosts
# the site's AJAX pagination endpoint, so it is deliberately NOT used here;
# this location page is server-rendered, listed in the sitemap, and lives
# outside the disallowed path. The server ignores ?p=N on this page (always
# returns page 1), and a page holds 15 results, so if Pakistan ever exceeds
# that a warning is logged instead of silently truncating.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


def _clean_location(raw: str) -> str:
    # The portal renders city + region even when they're identical
    # ("Islamabad, Islamabad") - collapse consecutive repeats for display.
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    deduped = [part for i, part in enumerate(parts) if i == 0 or part.lower() != parts[i - 1].lower()]
    return ", ".join(deduped) or "Not specified"


@register
class SecuritiScraper(Scraper):
    company_name = "Securiti (Veeam)"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(PAKISTAN_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        results_el = soup.select_one("#search-results")
        total_pages = results_el.get("data-total-pages") if results_el else None
        if total_pages and total_pages.isdigit() and int(total_pages) > 1:
            logger.warning(
                "%s has %s pages of results but only the first page is scraped - "
                "some Pakistan jobs are being missed",
                self.company_name,
                total_pages,
            )

        for item in soup.select("#search-results-list li"):
            link_el = item.select_one("a[href]")
            title_el = item.select_one(".job-list__title")
            if link_el is None or title_el is None:
                continue

            location_el = item.select_one(".job-list__location")
            location = _clean_location(location_el.get_text(strip=True)) if location_el else "Not specified"

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + link_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
