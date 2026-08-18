import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://yxcgwlnhrrneb36gzfdsfr5ahq0xnily.lambda-url.ca-central-1.on.aws/jobs/active"
CAREERS_URL = "https://www.kalsoft.com/careers/"
REQUEST_TIMEOUT_SECONDS = 10

# KalSoft's /careers/ page is a Next.js app that server-renders a "Loading
# job openings..." placeholder and fetches the real list client-side -
# found by pulling the page's own compiled JS chunk
# (_next/static/chunks/app/careers/page-*.js) and locating the fetch() call
# it makes: GET {this URL}, a public AWS Lambda Function URL, no auth
# required. The frontend has no per-job detail route at all (which job is
# selected is local React state, never reflected in the URL) - clicking a
# job just expands an inline application form on the same page, submitted
# to a separate endpoint carrying the job title as freeform text. So there
# is no real per-job "apply page" to link to; apply_link is built as the
# careers page with the job's own id as a query param - harmless (the page
# ignores unknown params and loads normally) and, unlike pointing every job
# at the same bare careers URL, keeps each job's apply_link unique, which
# the DB requires since it upserts jobs by apply_link.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class KalSoftScraper(Scraper):
    company_name = "KalSoft"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        jobs: list[Job] = []
        for item in payload.get("jobs", []):
            if item.get("isClosed"):
                continue

            jobs.append(
                Job(
                    title=item["name"],
                    company=self.company_name,
                    location=item.get("location") or "Not specified",
                    apply_link=f"{CAREERS_URL}?job={item['Id']}",
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
