import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://api.manatal.com/open/v3/career-page/bazaar-technologies/jobs/"
APPLY_URL = "https://www.careers-page.com/bazaar-technologies/job/{job_hash}"
REQUEST_TIMEOUT_SECONDS = 10

# Bazaar's careers page (bazaartech.com/careers) is client-rendered, but the
# page's own HTML embeds the Manatal ATS API URL it calls directly (no JS
# bundle digging needed this time), and separately embeds
# careers-page.com/bazaar-technologies/job/<hash> as the real apply link
# pattern - both confirmed by curling them directly. A few entries are
# generic "Bazaar Talent Pool - X" catch-alls (empty location, not a real
# opening - same pattern as Genetech's "Other Positions"), excluded here.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}
TALENT_POOL_PREFIX = "Bazaar Talent Pool"


@register
class BazaarTechnologiesScraper(Scraper):
    company_name = "Bazaar Technologies"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("results", []):
            title = item["position_name"]
            if title.startswith(TALENT_POOL_PREFIX):
                continue

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=item.get("location_display") or "Not specified",
                    apply_link=APPLY_URL.format(job_hash=item["hash"]),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
