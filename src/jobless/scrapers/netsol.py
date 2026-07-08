import logging
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Job, Scraper
from .registry import register

logger = logging.getLogger(__name__)

CAREERS_URL = "https://careers.netsoltech.com/openings/"
REQUEST_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_PAGES_SECONDS = 1
MAX_PAGES = 20

# NetSol's careers site (careers.netsoltech.com) is a self-hosted WordPress
# site built on NooTheme's "JobMonster" job-board theme (custom post type
# `noo_job`, listings inside a '<div class="noo-main">' container, individual
# postings rendered as '<article class="... noo_job ...">') - not a JS SPA
# and not a third-party ATS. Every open role is already present in the plain
# server-rendered HTML: the title sits in a nested
# '<h3 class="loop-item-title"><a href="...">', the job's own detail-page URL
# is also exposed on the article itself via a 'data-url' attribute, and the
# location sits in a sibling '<span class="job-location">' full of taxonomy
# links (confirmed directly against this site's own job-detail-page markup).
# Pagination follows standard WordPress '.../page/N/' links via an
# 'a.next.page-numbers' anchor inside the same container.
#
# robots.txt on this domain (https://careers.netsoltech.com/robots.txt) only
# defines a group for "Googlebot" ("Allow: /") - there is no "User-agent: *"
# group at all, so no crawl rules apply to a generic bot identifying itself
# honestly; nothing here is disallowed for us. Listings and job detail pages
# are publicly viewable with no login required. (careers.netsolpk.com, an
# older domain referenced in that robots.txt's sitemap line, 301-redirects
# to careers.netsoltech.com, so it isn't a separate live target.)
HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
    "Accept": "text/html",
}


@register
class NetSolScraper(Scraper):
    company_name = "NetSol Technologies"

    def scrape(self) -> list[Job]:
        jobs: list[Job] = []
        url: str | None = CAREERS_URL
        pages_fetched = 0

        while url and pages_fetched < MAX_PAGES:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            pages_fetched += 1

            soup = BeautifulSoup(response.text, "lxml")
            main = soup.find("div", class_="noo-main")
            if main is None:
                logger.warning("noo-main container not found on %s", url)
                break

            articles = main.find_all("article", class_="noo_job")
            if not articles:
                # No matching post-class articles - either the theme markup
                # shifted slightly, or (commonly) there are simply zero open
                # roles right now, in which case there are no <article> tags
                # at all and this is just an empty page, not an error.
                articles = main.find_all("article")

            for article in articles:
                title_el = article.select_one(".loop-item-title a") or article.select_one("h3 a, h2 a")
                if title_el is None or not title_el.get("href"):
                    continue

                apply_link = article.get("data-url") or title_el["href"]

                location_el = article.select_one(".job-location")
                if location_el is not None:
                    link_texts = [a.get_text(strip=True) for a in location_el.find_all("a")]
                    location = ", ".join(t for t in link_texts if t) or location_el.get_text(strip=True)
                else:
                    location = "Not specified"

                jobs.append(
                    Job(
                        title=title_el.get_text(strip=True),
                        company=self.company_name,
                        location=location or "Not specified",
                        apply_link=apply_link.strip(),
                        date_scraped=date.today(),
                    )
                )

            next_el = main.select_one(".pagination a.next")
            url = next_el["href"].strip() if next_el is not None and next_el.get("href") else None

            if url:
                time.sleep(DELAY_BETWEEN_PAGES_SECONDS)

        logger.info("scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs
