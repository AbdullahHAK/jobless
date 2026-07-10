import logging
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://next.invozone.com/jobs"
DETAIL_URL_TEMPLATE = "https://next.invozone.com/{job_id}"
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_PAGES_SECONDS = 1

# InvoZone's marketing site (invozone.com) explicitly disallows /jobs/ in
# robots.txt and only shows "Loading openings..." client-side anyway. The
# real job board lives on a separate subdomain, next.invozone.com/jobs,
# which has no robots.txt at all (empty file = no restrictions) and renders
# every job card directly in the initial server response - no JS rendering
# needed to see the list. Each card is a clickable
# '<div id="{slug}" name="card">' whose only click handler is jQuery's
# `window.location.href = this.id`, so the id attribute IS a relative path
# to that job's own detail page (confirmed by clicking cards in a one-off
# Playwright check - ids aren't a uniform slug format, some are plain
# "title-timestamp" strings and at least one is a nested "jobs/x/y" path,
# but in every case `id` is exactly the path the site itself navigates to).
# Pagination is a plain "?page=N" query string; we stop once a page returns
# zero job cards.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class InvoZoneScraper(Scraper):
    company_name = "InvoZone"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        page_number = 1

        while True:
            response = requests.get(
                CAREERS_URL,
                params={"page": page_number},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            cards = soup.select('div[name="card"]')
            if not cards:
                break

            for card in cards:
                job_id = card.get("id")
                title_el = card.select_one("h4.jobs-page")
                if not job_id or title_el is None:
                    continue

                location = "Not specified"
                for detail in card.select("div.mt-3.flex.align-items-center"):
                    if detail.select_one('use[href="#icon-branch"]') is not None:
                        continue  # this one is the department line, not location
                    text = detail.get_text(strip=True)
                    if text:
                        location = text
                        break

                jobs.append(
                    Job(
                        title=title_el.get_text(strip=True),
                        company=self.company_name,
                        location=location,
                        apply_link=DETAIL_URL_TEMPLATE.format(job_id=job_id),
                        date_scraped=date.today(),
                    )
                )

            page_number += 1
            time.sleep(DELAY_BETWEEN_PAGES_SECONDS)

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
