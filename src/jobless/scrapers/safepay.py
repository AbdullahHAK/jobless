import html
import json
import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

BASE_URL = "https://www.ycombinator.com"
CAREERS_URL = f"{BASE_URL}/companies/safepay/jobs"
REQUEST_TIMEOUT_SECONDS = 10

# Safepay (Karachi, YC-backed payments gateway) has no dedicated careers
# page of its own - Y Combinator's own company-jobs page is its real,
# primary hiring channel, the same role a third-party ATS like Greenhouse/
# Lever plays for other companies here. The page embeds a server-rendered
# `"jobPostings":[...]` JSON array as an HTML-entity-escaped attribute
# value (not a clean <script type="application/json"> block), so this
# HTML-unescapes the page first, then locates that array by matching
# bracket depth (robust against the many other nested fields in each
# posting - skills lists, etc. - that a naive per-field regex could trip
# on) and parses it as real JSON rather than regexing individual fields.
# robots.txt disallows /companies?* (a query-string search) and a few
# unrelated paths, not a specific company's /companies/<slug>/jobs page.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


def _extract_job_postings(page_html: str) -> list[dict]:
    unescaped = html.unescape(page_html)
    marker = '"jobPostings":['
    start_idx = unescaped.find(marker)
    if start_idx == -1:
        return []

    array_start = start_idx + len(marker) - 1  # include the opening '['
    depth = 0
    for i, char in enumerate(unescaped[array_start:], start=array_start):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return json.loads(unescaped[array_start : i + 1])
    return []


@register
class SafepayScraper(Scraper):
    company_name = "Safepay"

    def scrape(self) -> list[Job]:
        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        jobs: list[Job] = []
        for posting in _extract_job_postings(response.text):
            location = posting.get("location") or ""
            if "pakistan" not in location.lower():
                continue

            url = posting.get("url")
            title = posting.get("title")
            if not url or not title:
                continue

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=location,
                    apply_link=BASE_URL + url,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
