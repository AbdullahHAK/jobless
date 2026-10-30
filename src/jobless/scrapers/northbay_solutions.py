import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

# NorthBay's own careers page (/careers/) no longer even renders its job
# shortcode server-side - but the location-filtered page (/jobs/?loc=...)
# loads a self-hosted "/lever/" JS folder (not actually Lever.co - just
# named after it) that calls Resumator/JazzHR's real API directly, with an
# API key the company itself ships in that public, unauthenticated JS file.
# Same ATS family/pattern already used elsewhere in this fleet for an
# embedded-key-in-public-JS case (Bazaar Technologies' Manatal URL,
# KalSoft's Lambda URL) - the key isn't secret, it's shipped to every
# visitor's browser already. A handful of titles come back with a mangled
# en-dash (source-side mojibake, confirmed not a decoding bug on our end -
# same category as Avanceon's/CureMD's existing encoding artifacts) - left
# as-is rather than guessed-and-fixed.
JOBS_API_URL = "https://api.resumatorapi.com/v1/jobs/status/open?apikey=9xmcuwVUT7G1mbVPmcL25yZ74FLkAqq8"
APPLY_BASE_URL = "https://northbay.applytojob.com/apply"
REQUEST_TIMEOUT_SECONDS = 10

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class NorthBaySolutionsScraper(Scraper):
    company_name = "NorthBay Solutions"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload:
            # country_id is the clean, authoritative field (confirmed 59
            # real PK postings) - some non-PK-tagged postings mention
            # Pakistani cities in their free-text description too (cross-
            # posted/remote-eligible roles), but matching on that text
            # would risk false positives, so country_id alone is trusted.
            if item.get("country_id") != "Pakistan":
                continue

            city = item.get("city") or ""
            location = f"{city}, Pakistan" if city else "Pakistan"

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company_name,
                    location=location,
                    apply_link=f"{APPLY_BASE_URL}/{item['board_code']}",
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
