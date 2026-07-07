import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://folio3.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# Folio3's careers page is a plain server-rendered WordPress page, not a JS
# SPA and not backed by any third-party ATS: every open role is already
# present in the initial HTML response as a
# '<div class="jobs-box acc__card" data-location="..." data-type="...">'
# card, with the job title in a nested <h1 class="acc__title"> and a direct
# "Apply Now" link to the job's own page on folio3.com. There's no
# pagination (all current openings render on the single /careers/ page), so
# one requests.get + BeautifulSoup parse is enough - no API to
# reverse-engineer, no browser rendering needed.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class Folio3Scraper(Scraper):
    company_name = "Folio3"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        for card in soup.find_all("div", class_="jobs-box"):
            title_el = card.find("h1", class_="acc__title")
            apply_el = card.select_one("p.apply-btn a")
            if title_el is None or apply_el is None or not apply_el.get("href"):
                continue

            location = (card.get("data-location") or "").strip() or "Not specified"

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=apply_el["href"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
