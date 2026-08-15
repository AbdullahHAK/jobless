import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.genetechsolutions.com/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# The jobs page server-renders every posting as a
# <div class="job-opened job-area-trigger"> card (title in <h3>, location in
# a <h4 class="sub-text">, and a same-page anchor apply link already
# provided by the page's own share-widget as data-url - no need to hand-roll
# the title-to-slug conversion ourselves). One card is always "Other
# Positions" - a generic year-round "submit your resume" catch-all the site
# itself describes as a fallback, not a real opening - so it's explicitly
# excluded. robots.txt allows /jobs (only disallows a handful of unrelated
# paths).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
OTHER_POSITIONS_TITLE = "Other Positions"


@register
class GenetechSolutionsScraper(Scraper):
    company_name = "Genetech Solutions"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for card in soup.select("div.job-opened.job-area-trigger"):
            title_el = card.find("h3")
            if title_el is None:
                continue
            title = title_el.get_text(strip=True)
            if title == OTHER_POSITIONS_TITLE:
                continue

            location_el = card.find("h4", class_="sub-text")
            url_el = card.select_one(".job_social_share[data-url]")
            if url_el is None:
                continue

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location_el.get_text(strip=True) if location_el else "Not specified",
                    apply_link=url_el["data-url"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
