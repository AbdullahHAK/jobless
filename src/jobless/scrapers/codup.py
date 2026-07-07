import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://codup.applytojob.com/"
REQUEST_TIMEOUT_SECONDS = 10

# Codup's own site (codup.co/careers/) only embeds a JazzHR "basic widget"
# <script> (app.jazz.co/widgets/basic/create/codup) that document.write()s the
# job list client-side. Rather than depend on that JS shim, we go straight to
# the JazzHR-hosted career page it points at - codup.applytojob.com - which is
# plain server-rendered HTML (no SPA, no JSON API, no auth) containing every
# open role as a '<li class="list-group-item">' with the title in a nested
# '<h3 class="list-group-item-heading"><a href="...">' and the location in the
# following '<ul class="list-inline list-group-item-text"><li>' text. There's
# no pagination - all current openings render on this single page.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class CodupScraper(Scraper):
    company_name = "Codup"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        for item in soup.select("ul.list-group li.list-group-item"):
            title_el = item.select_one("h3.list-group-item-heading a")
            if title_el is None or not title_el.get("href"):
                continue

            location_el = item.select_one("ul.list-group-item-text li")
            location = location_el.get_text(strip=True) if location_el else "Not specified"

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=title_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
