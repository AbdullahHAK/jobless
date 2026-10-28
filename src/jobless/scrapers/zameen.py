import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://zameen.breezy.hr"
CAREERS_URL = f"{BASE_URL}/"
REQUEST_TIMEOUT_SECONDS = 10

# Breezy-hosted careers page, same pattern as Avanceon/Dubizzle/Strategic
# Systems International. Zameen.com is Pakistan's largest real-estate
# classifieds portal - every posting's location resolves to a single
# Pakistani city ending in ", PK", so postings are kept on that suffix the
# same way Avanceon's board is filtered. Role mix here skews heavily
# non-engineering (sales, construction/QAQC, property management, customer
# support) since this is the real-estate-and-construction-services arm
# hiring, not a software team - kept anyway, same "accept a thinner/less
# engineering-heavy board for a real, well-known company" tradeoff already
# made for a few other tracked companies. Unlike Avanceon's board, postings
# here aren't repeated per-location-grouping (72 postings, 72 unique
# hrefs confirmed), but entries are still deduped by href defensively.
# robots.txt only disallows static-asset paths and AhrefsBot specifically.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class ZameenScraper(Scraper):
    company_name = "Zameen.com"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        seen_links: set[str] = set()

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        for item in soup.select("li.position"):
            location_el = item.select_one(".location span")
            location = location_el.get_text(strip=True) if location_el else None
            if location is None or not location.endswith(", PK"):
                continue

            link_el = item.select_one(".position-details a[href]")
            title_el = link_el.find("h2") if link_el else None
            if link_el is None or title_el is None:
                continue

            href = link_el["href"]
            if href in seen_links:
                continue
            seen_links.add(href)

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + href,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
