import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://trangotech.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# The careers page renders the same job list four times (once per "Filter
# by"/"Function"/"Location"/"Experience" tab), so only the first tab pane
# (id="cross-plat-A", the one shown by default) is parsed to avoid
# duplicates. Each job is a <button class="collapsible"> with title/location
# spans, wired via data-bs-target to a Bootstrap modal containing an
# <iframe data-lzl-src="..."> that lazy-loads the real external apply form
# (their HRMS, eplanetcom.com) - that lazy-load src is the actual apply
# link, not the modal itself. Confirmed via robots.txt: broad "Allow: /".
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class TrangoTechScraper(Scraper):
    company_name = "Trango Tech"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        container = soup.find(id="cross-plat-A")
        if container is None:
            logger.warning("cross-plat-A container not found on %s", CAREERS_URL)
            return jobs

        for button in container.select("button.collapsible"):
            title_el = button.select_one(".txt-left")
            location_el = button.select_one(".txt-right")
            if title_el is None:
                continue

            apply_btn = button.find_next("button", attrs={"data-bs-target": True})
            if apply_btn is None:
                continue
            modal = soup.find(id=apply_btn["data-bs-target"].lstrip("#"))
            iframe = modal.select_one("iframe[data-lzl-src]") if modal else None
            if iframe is None:
                continue

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location_el.get_text(strip=True) if location_el else "Not specified",
                    apply_link=iframe["data-lzl-src"].strip(),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
