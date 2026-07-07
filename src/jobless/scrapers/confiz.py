import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

# Confiz's official careers page (https://confiz.com/careers/) links out
# entirely to a Simplicant-hosted job board (https://confiz.simplicant.com/)
# for job listings and applications. That page is plain, server-rendered
# HTML - the whole current job list (grouped by location) is already present
# in the initial response, no JS rendering or hidden API needed, so a single
# requests.get + BeautifulSoup parse is enough.
#
# The page also shows a "Our Featured Jobs" section up top that duplicates a
# subset of the same postings shown further down in their per-location
# groups; we only parse the per-location groups (skipping the featured
# heading) so each job is only returned once.
JOBS_URL = "https://confiz.simplicant.com/"
REQUEST_TIMEOUT_SECONDS = 10

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


def _absolute_url(href: str) -> str:
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("/"):
        return f"https://confiz.simplicant.com{href}"
    return href


@register
class ConfizScraper(Scraper):
    company_name = "Confiz"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(JOBS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        for heading in soup.select("h2.heading"):
            if "heading-featured" in heading.get("class", []):
                continue  # skip the duplicate "Our Featured Jobs" section

            location = heading.get_text(strip=True)
            group = heading.find_next_sibling("div", class_="list-group")
            if group is None:
                continue

            for item in group.select("a.list-group-item"):
                href = item.get("href")
                title_el = item.select_one(".job-title")
                if not href or not title_el:
                    continue

                apply_link = _absolute_url(href)
                if apply_link in seen_links:
                    continue
                seen_links.add(apply_link)

                jobs.append(
                    Job(
                        title=title_el.get_text(strip=True),
                        company=self.company_name,
                        location=location,
                        apply_link=apply_link,
                        date_scraped=date.today(),
                    )
                )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
