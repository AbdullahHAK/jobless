import logging
import re
from datetime import date
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://careers.foodpanda.com"
VACANCIES_SITEMAP_URL = f"{BASE_URL}/vacanciessitemap.xml"
REQUEST_TIMEOUT_SECONDS = 10

# foodpanda's Attrax-powered careers site has no server-rendered "all
# Pakistan jobs" page reachable without reverse-engineering its search
# widget's AJAX filter - and robots.txt explicitly disallows the one path
# that would otherwise work (`Disallow: /jobs?*`). The vacancies sitemap
# (not disallowed) lists every live job URL directly instead, with the
# country baked into each URL's own slug (e.g. "-in-karachi-pakistan-jid-
# 3304") - matching on that is both compliant and simpler than fighting
# the widget. Each job's own page is still fetched individually (cheap,
# ~20 postings) since the sitemap carries no title/location, just the URL;
# its <title> tag reliably reads "{title} job in {location} | foodpanda".
# Role mix here is almost entirely ops/sales/finance, not engineering - a
# conscious, discussed tradeoff for a real, massively well-known company
# (same "accept a thinner board" precedent as Zameen.com/Bank Alfalah-style
# companies elsewhere in this fleet), not a scraper miss.
TITLE_TAG_PATTERN = re.compile(r"^(.*) job in (.*) \| foodpanda$")
PAKISTAN_JOB_URL_PATTERN = re.compile(r"-pakistan-jid-\d+$")

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _job_title_and_location(detail_url: str) -> tuple[str, str] | None:
    response = requests.get(detail_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    if soup.title is None:
        return None

    match = TITLE_TAG_PATTERN.match(soup.title.get_text(strip=True))
    if match is None:
        return None
    return match.group(1), match.group(2)


@register
class FoodpandaScraper(Scraper):
    company_name = "foodpanda"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(VACANCIES_SITEMAP_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)
        for loc_el in root.findall("sm:url/sm:loc", SITEMAP_NAMESPACE):
            url = loc_el.text or ""
            if not PAKISTAN_JOB_URL_PATTERN.search(url):
                continue

            title_and_location = _job_title_and_location(url)
            if title_and_location is None:
                continue
            title, location = title_and_location

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    apply_link=url,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
