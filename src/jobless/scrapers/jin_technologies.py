import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://jintech.com"
CAREERS_URL = f"{BASE_URL}/careers"
REQUEST_TIMEOUT_SECONDS = 10

# WordPress + WPBakery site (no ATS vendor at all). The careers page lays
# out openings in a fixed 3-column grid, one column per office city
# (Islamabad, Karachi, Multan) - each column has an <h5> city heading
# followed by a <p><a><strong>Title</strong></a></p> per open role, or a
# "We don't have any open positions..." sentence when that city has none.
# Every office is in Pakistan, so no further location filtering is needed.
# Each job title links to its own dedicated WordPress page (e.g.
# /software-engineer/), which doubles as the apply page. Parsing is scoped
# to the specific grid row that follows the "current vacancies available"
# heading, since the page also has unrelated <h5> tags for benefits/perks
# elsewhere. robots.txt only disallows /wp-admin/ (admin-ajax excepted).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@register
class JinTechnologiesScraper(Scraper):
    company_name = "Jin Technologies"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        heading = soup.find(string=lambda s: s and "current vacancies" in s.lower())
        if heading is None:
            logger.warning("could not find vacancies heading for %s", self.company_name)
            return jobs

        heading_row = heading.find_parent("div", class_="vc_row")
        grid_row = heading_row.find_next_sibling("div", class_="vc_row") if heading_row else None
        if grid_row is None:
            logger.warning("could not find vacancies grid for %s", self.company_name)
            return jobs

        for h5 in grid_row.find_all("h5"):
            city = h5.get_text(strip=True)
            column = h5.find_parent("div", class_="vc_column_container")
            if column is None:
                continue

            for link_el in column.select("p a[href]"):
                strong_el = link_el.find("strong")
                title = strong_el.get_text(strip=True) if strong_el else link_el.get_text(strip=True)
                if not title:
                    continue

                jobs.append(
                    Job(
                        title=title,
                        company=self.company_name,
                        location=f"{city}, Pakistan",
                        apply_link=link_el["href"],
                        date_scraped=date.today(),
                    )
                )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
