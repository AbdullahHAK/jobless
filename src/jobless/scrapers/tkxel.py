import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://careers.tkxel.com/jobs/"
REQUEST_TIMEOUT_SECONDS = 10

# Tkxel's careers page is a plain server-rendered WordPress page (theme
# "tkxel-careers"), not a JS SPA - every open role is already present in the
# initial HTML response inside a '<div class="jobs-cards-wrp">' container as
# '<div class="job-card"><a href="...">' entries, with the title in a nested
# '<div class="job-title"><h6>' and the location in a sibling
# '<div class="job-location"><p>'. The "Apply"/card link already points
# straight to the specific job posting on Tkxel's ATS (Zoho Recruit, mapped
# to the custom domain jobs.tkxel.com) - that path is explicitly allowed for
# all crawlers in jobs.tkxel.com's robots.txt ("Allow: /jobs", "Allow:
# /jobs/*"), so we can just use that URL directly as apply_link without ever
# visiting it ourselves. There's no pagination (all current openings render
# on the single /jobs/ page), so one requests.get + BeautifulSoup parse is
# enough - no API to reverse-engineer, no browser rendering needed.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class TkxelScraper(Scraper):
    company_name = "Tkxel"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        for card in soup.find_all("div", class_="job-card"):
            apply_el = card.find("a", href=True)
            title_el = card.select_one(".job-title h6")
            location_el = card.select_one(".job-location p")
            if apply_el is None or title_el is None:
                continue

            location = location_el.get_text(strip=True) if location_el else "Not specified"
            if not location:
                location = "Not specified"

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
