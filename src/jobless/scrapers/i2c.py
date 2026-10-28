import json
import logging
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://careers.i2cinc.com"
CAREERS_PAGE_URL = f"{BASE_URL}/careers/"
AJAX_URL = f"{BASE_URL}/ajax.php"
REQUEST_TIMEOUT_SECONDS = 10

# i2c Inc's own custom-built careers portal (not a recognized ATS vendor) -
# a US-HQ'd card-issuing/digital-banking platform with a large Lahore
# engineering center. The job list isn't in the page's own HTML; it's
# fetched by the page's own JS via a POST to /ajax.php (f=getJobsPager)
# carrying a CSRF token scraped from a hidden <input> on the page and the
# location filter as a JSON string. Replicating that exact request (same
# pattern the page's own jQuery does) returns an HTML fragment of job
# tiles, server-side filtered to Pakistan already - no further location
# filtering needed on our end. One real gotcha: a bare `requests` User-
# Agent with no Accept/Accept-Language headers gets back a page missing
# the CSRF form entirely (unclear why - not an explicit bot-block, since
# our own identified UA plus standard headers works fine). robots.txt
# 404s on this subdomain (no file at all - unrestricted).
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
AJAX_HEADERS = {
    **HEADERS,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

CSRF_TOKEN_PATTERN = re.compile(r'name="csrf_token" value="([^"]+)"')


@register
class I2cScraper(Scraper):
    company_name = "i2c Inc"

    def scrape(self) -> list[Job]:
        session = requests.Session()

        page_response = session.get(CAREERS_PAGE_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        page_response.raise_for_status()

        token_match = CSRF_TOKEN_PATTERN.search(page_response.text)
        if token_match is None:
            logger.warning(
                "could not find csrf_token on %s - skipping %s", CAREERS_PAGE_URL, self.company_name
            )
            return []

        payload = {
            "f": "getJobsPager",
            "filters": json.dumps({"location": ["Pakistan"]}),
            "s": "",
            "csrf_token": token_match.group(1),
        }
        ajax_response = session.post(
            AJAX_URL, data=payload, headers=AJAX_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
        )
        ajax_response.raise_for_status()
        data = ajax_response.json()

        jobs: list[Job] = []
        soup = BeautifulSoup(data.get("html", ""), "lxml")
        for tile in soup.select(".job-tile"):
            link_el = tile.select_one("a[href]")
            title_el = tile.select_one("h2")
            location_el = tile.select_one(".joblisting-location")
            if link_el is None or title_el is None or location_el is None:
                continue

            jobs.append(
                Job(
                    title=title_el.get_text(strip=True),
                    company=self.company_name,
                    location=location_el.get_text(strip=True),
                    apply_link=f"{BASE_URL}/careers/{link_el['href']}",
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
