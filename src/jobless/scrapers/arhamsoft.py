import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://career.arhamsoft.com"
CAREERS_URL = f"{BASE_URL}/careers"
REQUEST_TIMEOUT_SECONDS = 10

# ArhamSoft's own self-built "ArhamSoft ATS" (static-exported Next.js) -
# a small Lahore-based Pakistani software house, but one with a New York
# office too (per the footer contact address), so location isn't assumed.
# Unlike every other scraper here, the list page's job cards don't carry a
# location at all (just experience level + open position count) - only
# each job's own detail page has a real City/Country <dl>. Since this
# company only ever has a handful of postings, fetching each job's detail
# page too (one extra request per job) is cheap and gets a real verified
# location instead of guessing one from the company's registered address.
# career.arhamsoft.com has no robots.txt at all (404 -> unrestricted).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


def _job_location(detail_url: str) -> str | None:
    response = requests.get(detail_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    city = country = None
    for dt in soup.select("dt"):
        label = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")
        value = dd.get_text(strip=True) if dd else None
        if label == "City":
            city = value
        elif label == "Country":
            country = value

    if country is None or "pakistan" not in country.lower():
        return None
    return f"{city}, {country}" if city else country


@register
class ArhamSoftScraper(Scraper):
    company_name = "ArhamSoft"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for link_el in soup.select('h3.mini-sub-heading a[href^="/careers/"]'):
            detail_url = BASE_URL + link_el["href"]
            location = _job_location(detail_url)
            if location is None:
                continue

            jobs.append(
                Job(
                    title=link_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=detail_url,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
