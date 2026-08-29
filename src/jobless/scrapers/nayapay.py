import logging
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.nayapay.com/careers"
REQUEST_TIMEOUT_SECONDS = 10

# The careers page server-renders each opening as a
# <div class="job-postion-card-holder"> - title in <h5 class="semi-bold">,
# location in <h5 class="position-location"> (blank for some postings, kept
# as-is). NayaPay's real "apply" mechanism is a mailto: link (email your
# resume with the job title as the subject), which Job.apply_link (a
# pydantic HttpUrl) can't hold - same situation as Kalsoft/Genetech/Trango
# Tech, so apply_link points at the careers page instead, anchored to the
# job's own slug for uniqueness. robots.txt only disallows /.well-known.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    return _SLUG_RE.sub("-", title.lower()).strip("-")


@register
class NayaPayScraper(Scraper):
    company_name = "NayaPay"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for card in soup.select("div.job-postion-card-holder"):
            title_el = card.select_one("h5.semi-bold")
            if title_el is None:
                continue
            title = title_el.get_text(strip=True)

            location_el = card.select_one("h5.position-location")
            location = location_el.get_text(strip=True) if location_el else ""

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location or "Not specified",
                    apply_link=f"{CAREERS_URL}#{_slugify(title)}",
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
