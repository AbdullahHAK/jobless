import json
import logging
from datetime import date
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://pktechcareers-ibex.icims.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
REQUEST_TIMEOUT_SECONDS = 10

# ibex (NASDAQ: IBEX) runs two separate iCIMS career sites for its Pakistan
# operations: pkcareers-ibex.icims.com (BPO/customer-support roles) and this
# one, pktechcareers-ibex.icims.com, dedicated to its Pakistan tech/
# engineering org - only this board is scraped, to keep this a software-
# roles board like the rest of the fleet. robots.txt only disallows
# referral/login/candidate/reminder paths and publishes its own sitemap,
# which lists every live job URL directly. Each job page then embeds a
# standard schema.org JobPosting in a <script type="application/ld+json">
# tag (title + jobLocation), so no HTML-structure scraping is needed. A
# posting that's actually been pulled returns 410 Gone instead of
# rendering - skipped like any other failed per-job fetch.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _job_posting(job_url: str) -> dict | None:
    try:
        response = requests.get(job_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.HTTPError:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    script = soup.find("script", type="application/ld+json")
    if script is None or script.string is None:
        return None
    return json.loads(script.string)


@register
class IbexScraper(Scraper):
    company_name = "ibex"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        root = ElementTree.fromstring(response.content)
        for loc_el in root.findall("sm:url/sm:loc", SITEMAP_NAMESPACE):
            url = loc_el.text or ""
            if not url.endswith("/job"):
                continue

            posting = _job_posting(url)
            if posting is None:
                continue

            locations = posting.get("jobLocation") or [{}]
            address = locations[0].get("address", {})
            location = address.get("addressLocality") or "Pakistan"

            jobs.append(
                Job(
                    title=posting["title"],
                    company=self.company_name,
                    location=location,
                    apply_link=posting.get("url", url),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
