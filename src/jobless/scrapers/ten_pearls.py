import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://api.resumatorapi.com/v1/jobs"
APPLY_URL = "https://10pearls.applytojob.com/apply/jobs/details/{job_id}"
REQUEST_TIMEOUT_SECONDS = 10

# 10Pearls' careers hub (https://10pearls.com/join-our-team/) links out to per-location
# pages such as https://10pearls.com/karachi-job-openings/. Each of those pages renders its
# job list with a small inline script that fetches the full company-wide job list from this
# JazzHR/Resumator API endpoint and then filters it client-side (by status and by city) before
# building the DOM. The API key below is not a secret we reverse-engineered - it is embedded
# directly, in plain text, in that page's own publicly served HTML/JS, so it is sent to every
# anonymous visitor's browser already. We call the same endpoint with the same key instead of
# driving a full browser just to re-render it, and we reproduce their "status == Open" filter
# ourselves (some entries returned by the API are unpublished "Drafting" postings, which we
# exclude, matching what the site itself shows to visitors). No login or cookies are involved.
API_KEY = "jB0b57gnKdU9rqBWvqQpxzITAPrHUFaz"
OPEN_STATUS = "Open"

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class TenPearlsScraper(Scraper):
    company_name = "10Pearls"

    def scrape(self) -> list[Job]:
        response = requests.get(
            JOBS_API_URL,
            params={"apikey": API_KEY},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload:
            if item.get("status") != OPEN_STATUS:
                continue

            location = (
                item.get("city") or item.get("state") or item.get("country_id") or "Not specified"
            )

            jobs.append(
                Job(
                    title=item["title"],
                    company=self.company_name,
                    location=location,
                    apply_link=APPLY_URL.format(job_id=item["id"]),
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
