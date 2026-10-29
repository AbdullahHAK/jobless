import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_SITE_URL = "https://careers.nayatel.com"
JOBS_API_URL = "https://careersapi.nayatel.com/jobs/getAllJobs"
REQUEST_TIMEOUT_SECONDS = 10

# NayaTel's own custom-built careers portal (a Create React App SPA, not a
# recognized ATS vendor) - a large Islamabad-HQ'd fiber ISP/telecom. The
# portal's own job list isn't server-rendered; it's fetched by the app's
# own code via an unauthenticated POST (no request body, just a Content-
# Type header) to a dedicated API subdomain, found by pulling the SPA's
# compiled JS bundle and searching for where its base-URL constant gets
# used - same "read the compiled bundle" technique already used for
# KalSoft/Xgrid-style investigations. NayaTel operates only within
# Pakistan, so every posting here is already Pakistan-based - no further
# location filtering needed. Apply links are built from the SPA's own
# `vacant-positions/:jid` route (confirmed in the same bundle), since the
# API response carries no direct apply URL field. Neither
# careers.nayatel.com (robots.txt explicitly allows all) nor
# careersapi.nayatel.com (no robots.txt at all - a pure API host) restrict
# this.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Content-Type": "application/json",
}


@register
class NayatelScraper(Scraper):
    company_name = "Nayatel"

    def scrape(self) -> list[Job]:
        response = requests.post(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("data", []):
            job_id = item.get("ID")
            title = item.get("JOBTITLE")
            if job_id is None or not title:
                continue

            city = item.get("JOBLOCATION") or "Pakistan"
            location = f"{city}, Pakistan" if city != "Pakistan" else city

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    apply_link=f"{CAREERS_SITE_URL}/vacant-positions/{job_id}",
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
