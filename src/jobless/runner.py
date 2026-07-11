import logging

from . import db, scrapers  # noqa: F401 - import triggers scraper auto-registration
from .scrapers.base import Job
from .scrapers.registry import all_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_all() -> list[Job]:
    """Run every registered scraper. A single scraper failing is logged and
    skipped so it doesn't take down the rest of the run."""
    jobs: list[Job] = []
    for scraper_cls in all_scrapers():
        scraper = scraper_cls()
        try:
            jobs.extend(scraper.scrape())
        except Exception:
            logger.exception("scraper %s failed", scraper_cls.company_name)
    return jobs


def main() -> None:
    jobs = run_all()
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
    finally:
        conn.close()
