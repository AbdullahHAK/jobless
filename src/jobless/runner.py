import logging

from . import db, scrapers  # noqa: F401 - import triggers scraper auto-registration
from .scrapers.base import Job
from .scrapers.registry import all_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_all() -> tuple[list[Job], set[str]]:
    """Run every registered scraper. A single scraper failing is logged and
    skipped so it doesn't take down the rest of the run. Also returns which
    companies' scrapers actually succeeded - needed by the caller to safely
    prune closed listings without wrongly wiping out a company's postings
    just because its scraper failed this run (see db.close_stale_jobs)."""
    jobs: list[Job] = []
    succeeded_companies: set[str] = set()
    for scraper_cls in all_scrapers():
        scraper = scraper_cls()
        try:
            jobs.extend(scraper.scrape())
            succeeded_companies.add(scraper_cls.company_name)
        except Exception:
            logger.exception("scraper %s failed", scraper_cls.company_name)
    return jobs, succeeded_companies


def main() -> None:
    jobs, succeeded_companies = run_all()
    logger.info("scraped %d jobs total", len(jobs))
    for job in jobs:
        print(f"{job.company} | {job.title} | {job.location} | {job.apply_link}")

    try:
        conn = db.get_connection()
    except Exception:
        logger.exception("could not connect to the database; skipping persistence")
        return

    try:
        db.init_db(conn)
        db.save_jobs(conn, jobs)

        active_links_by_company: dict[str, list[str]] = {}
        for job in jobs:
            active_links_by_company.setdefault(job.company, []).append(str(job.apply_link))

        for company in succeeded_companies:
            closed = db.close_stale_jobs(conn, company, active_links_by_company.get(company, []))
            if closed:
                logger.info("marked %d stale job(s) closed for %s", closed, company)
    finally:
        conn.close()
