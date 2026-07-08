import logging
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://new.careers.kualitatem.com/"
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_REQUESTS_SECONDS = 1
DEFAULT_LOCATION = "Not specified"

# Kualitatem's careers portal (new.careers.kualitatem.com, linked from the
# "Careers" item in www.kualitatem.com's own footer) is a plain
# server-rendered Laravel app - not a JS SPA and not backed by any
# third-party ATS. Every open role is already present in the initial HTML
# response of the home page as a '<div class="job-card">' with the title in
# a nested '.job-title' element and an "APPLY NOW" link
# ('<a class="apply-btn" href="...">') straight to that job's own detail page
# at /job/<id>. There's no pagination - all current openings render on the
# single home page (confirmed empty robots.txt "Disallow:" for this host, and
# both the listing and every detail page load fully for an anonymous request
# with no cookies/login).
#
# The listing cards don't include a location, though, so for each job we make
# one additional request to its own detail page, which is likewise plain
# server-rendered HTML containing a '<ul class="job-info"><li>Location:
# ...</li></ul>' block. No API to reverse-engineer, no browser rendering
# needed - just one GET per job, rate-limited like any other paginated
# scraper here.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class KualitatemScraper(Scraper):
    company_name = "Kualitatem"

    def scrape(self) -> list[Job]:
        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        listings: list[tuple[str, str]] = []
        for card in soup.select(".job-card"):
            if card.find_parent(class_="job-template"):
                continue  # hidden template card, not a real posting

            title_el = card.select_one(".job-title")
            apply_el = card.select_one("a.apply-btn")
            if title_el is None or apply_el is None or not apply_el.get("href"):
                continue

            listings.append((title_el.get_text(strip=True), apply_el["href"].strip()))

        jobs: list[Job] = []
        for index, (title, apply_link) in enumerate(listings):
            if index:
                time.sleep(DELAY_BETWEEN_REQUESTS_SECONDS)

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=self._fetch_location(apply_link),
                    apply_link=apply_link,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs

    @staticmethod
    def _fetch_location(job_detail_url: str) -> str:
        try:
            response = requests.get(job_detail_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException:
            logger.warning("failed to fetch job detail page %s; using default location", job_detail_url)
            return DEFAULT_LOCATION

        soup = BeautifulSoup(response.text, "lxml")
        for li in soup.select("ul.job-info li"):
            text = li.get_text(" ", strip=True)
            if text.lower().startswith("location:"):
                return text.split(":", 1)[1].strip() or DEFAULT_LOCATION

        return DEFAULT_LOCATION
