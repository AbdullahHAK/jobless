import json
import logging
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://www.euroshub.com/career"
REQUEST_TIMEOUT_SECONDS = 10

# EurosHub's careers page is a Next.js (App Router) page. It is *not* a
# client-side SPA that fetches jobs from a separate API after load - the full
# job list is already embedded in the server-rendered HTML, inside one of the
# React Server Component payload chunks that Next.js streams as
# `<script>self.__next_f.push([1, "<id>:<json>"])</script>` tags. One of
# those chunks decodes to a JSON array whose last element is an object
# `{"jobs": [...]}` with the complete, current listing (title, location,
# description, requirements, etc. per job) - so a single plain
# `requests.get` + parsing that one inline script is enough; no browser
# rendering and no separate API call are needed. (The site's own robots.txt
# only disallows `/api/`, which this never touches - we only fetch the
# public `/career` HTML page itself.)
#
# EurosHub has no per-job detail page or URL fragment: clicking a listing
# just expands an accordion in place (confirmed via a one-off Playwright
# check - the page URL never changes, and there is no unique HTML anchor id
# per job in the DOM). "Applying" happens through an in-page form on that
# same page rather than a distinct posting URL. So apply_link points every
# job at the careers page's own "open positions" anchor, which is the
# closest thing to a working, specific-to-the-posting URL that the site
# exposes.
APPLY_URL = f"{CAREERS_URL}#openings"

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}

_NEXT_F_PUSH_RE = re.compile(r"self\.__next_f\.push\(\[1,\s*(\".*\")\]\)", re.S)
_FLIGHT_ID_PREFIX_RE = re.compile(r"^[0-9a-zA-Z]+:")
_JOBS_KEY_RE = re.compile(r'"jobs"\s*:\s*\[')


def _extract_jobs(html: str) -> list[dict]:
    """Pull the `jobs` list out of the page's embedded RSC data chunk."""
    soup = BeautifulSoup(html, "lxml")

    for script in soup.find_all("script"):
        text = script.string or script.get_text()
        if not text or "__next_f" not in text:
            continue

        match = _NEXT_F_PUSH_RE.search(text)
        if not match:
            continue

        try:
            decoded = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        # `decoded` is the RSC chunk's raw (unescaped) string, e.g.
        # '1b:["$","$L21",null,{"jobs":[...]}]\n' - only one chunk actually
        # carries the job list, so skip the rest cheaply before parsing JSON.
        if not _JOBS_KEY_RE.search(decoded):
            continue

        body = _FLIGHT_ID_PREFIX_RE.sub("", decoded, count=1)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            continue

        if not isinstance(payload, list):
            continue

        for element in payload:
            if isinstance(element, dict) and "jobs" in element:
                return element["jobs"]

    return []


@register
class EurosHubScraper(Scraper):
    company_name = "EurosHub"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []

        response = requests.get(CAREERS_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        for item in _extract_jobs(response.text):
            title = item.get("title")
            if not title:
                continue

            jobs.append(
                Job(
                    title=title,
                    company=self.company_name,
                    location=item.get("location") or "Not specified",
                    apply_link=APPLY_URL,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
