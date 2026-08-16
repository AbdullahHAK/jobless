import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.dplit.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# DPL's careers page server-renders every opening as an
# <article class="career-job-card"> inside <ul class="career-jobs-grid">
# under the "#alljobs" tab pane. The same cards are duplicated under
# per-city tabs (e.g. "#islamabadjobs") for the site's own tab-filter UI -
# only "#alljobs" is parsed to get the complete list without duplicates.
# Title and the real apply link (their Zoho Recruit tenant,
# dplit.zohorecruit.com - a different, non-blocked tenant from the one
# ruled out for Techlogix) both live on the same
# <a class="career-job-card__title">; location comes from the "City" meta
# item. robots.txt only blocks WordPress admin/query paths, not /careers/.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}
CITY_LABEL = "City"


@register
class DPLScraper(Scraper):
    company_name = "DPL"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        container = soup.find(id="alljobs")
        if container is None:
            logger.warning("alljobs tab not found on %s", CAREERS_URL)
            return jobs

        for card in container.select("article.career-job-card"):
            title_el = card.select_one(".career-job-card__title")
            if title_el is None or not title_el.get("href"):
                continue

            location = "Not specified"
            for item in card.select(".career-job-card__meta-item"):
                label = item.select_one(".career-job-card__meta-label")
                if label and label.get_text(strip=True) == CITY_LABEL:
                    value = item.select_one(".career-job-card__meta-value")
                    if value:
                        location = value.get_text(strip=True)
                    break

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
