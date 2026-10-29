import concurrent.futures
import logging

import requests

from .scrapers.base import Job

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10
MAX_WORKERS = 8

# Status codes that definitively mean "this page is gone" - not 401/403
# (often just a WAF/bot-check reacting to our UA, not proof a real browser
# visitor would see nothing) and not 5xx/timeouts (a transient server
# hiccup isn't proof the listing closed). Caught for real on Educative:
# their public Lever board (jobs.lever.co/educative) was taken down
# entirely, but api.lever.co kept serving the same postings as if nothing
# had changed, so every "live" apply_link 404'd for real visitors with no
# way to tell from the API response alone.
DEAD_STATUS_CODES = {404, 410}

HEADERS = {
    "User-Agent": "JoblessBot/0.1 (+https://github.com/jobless; job board aggregator for PK software jobs)",
}


def _is_dead(apply_link: str) -> bool:
    try:
        with requests.get(
            apply_link, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS, stream=True
        ) as response:
            return response.status_code in DEAD_STATUS_CODES
    except requests.RequestException:
        # Network hiccup or timeout - not definitive proof the link is dead,
        # so err on the side of keeping the job rather than risking a false
        # positive that wipes out a real listing.
        return False


def filter_live_jobs(jobs: list[Job]) -> list[Job]:
    """Drop jobs whose apply_link no longer actually resolves. A scraper's
    own data source can drift from what's really live on the public page
    (see DEAD_STATUS_CODES above), so this re-checks every link itself
    rather than trusting the source API/page alone."""
    if not jobs:
        return jobs

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        dead_flags = list(executor.map(lambda job: _is_dead(str(job.apply_link)), jobs))

    live_jobs = [job for job, dead in zip(jobs, dead_flags) if not dead]

    dropped = len(jobs) - len(live_jobs)
    if dropped:
        logger.warning("dropped %d dead-link job(s) out of %d", dropped, len(jobs))
    return live_jobs
