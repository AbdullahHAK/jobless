import logging
from datetime import date

import requests

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

JOBS_API_URL = "https://apply.workable.com/api/v1/widget/accounts/pakistan-mobile-communication-limited-pmcl"
REQUEST_TIMEOUT_SECONDS = 10

# Jazz (PMCL) - Pakistan's largest mobile operator - hires through a
# Workable board branded "JazzWorld", linked directly from its own
# jazz.com.pk/careers redirect. Workable's public widget API, same pattern
# as Devsinc/Remotebase/Prime System Solutions/etc. Every posting is
# already Pakistan-based (a domestic telco, not a global employer), so no
# country filter is strictly needed - kept defensively anyway. Same
# multi-city quirk as Prime System Solutions: a role open in several
# Pakistani cities at once comes back as one row per city sharing the same
# application_url, so entries are grouped by that URL and their cities
# merged into one location string, rather than letting the DB's
# upsert-by-apply_link silently collapse them into whichever city happened
# to be scraped last. The board spans the whole JazzWorld group (telecom,
# JazzCash fintech, JazzSure insurance), so the role mix is mostly
# non-engineering (Finance/Legal/Sales) with a handful of genuine
# IT/engineering roles mixed in - the same "accept a less engineering-heavy
# board for a real, well-known company" tradeoff already made for
# Zameen.com/foodpanda.
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "application/json",
}


@register
class JazzScraper(Scraper):
    company_name = "Jazz"

    def scrape(self) -> list[Job]:
        response = requests.get(JOBS_API_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()

        grouped: dict[str, dict] = {}
        for item in payload.get("jobs", []):
            if item.get("country") != "Pakistan":
                continue

            url = item["application_url"]
            entry = grouped.setdefault(url, {"title": item["title"], "cities": set()})
            city = item.get("city")
            if city:
                entry["cities"].add(city)

        jobs: list[Job] = []
        for url, data in grouped.items():
            jobs.append(
                Job(
                    title=data["title"],
                    company=self.company_name,
                    location=", ".join(sorted(data["cities"])) or "Pakistan",
                    apply_link=url,
                    date_scraped=date.today(),
                )
            )

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
