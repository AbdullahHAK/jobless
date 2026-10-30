import logging

from . import (  # noqa: F401 - import triggers scraper auto-registration
    alerts,
    db,
    link_health,
    scraper_health,
    scrapers,
)
from .scrapers.base import Job
from .scrapers.registry import all_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_all() -> tuple[list[Job], dict[str, int | None]]:
    """Run every registered scraper. A single scraper failing is logged and
    skipped so it doesn't take down the rest of the run. Each scraper's own
    jobs are also re-validated against link_health.filter_live_jobs before
    being kept, since a scraper's source API/page can drift from what's
    really live (see link_health for why). Also returns each company's job
    count (None if its scraper raised) - the caller feeds this into
    scraper_health.evaluate to decide whether it's safe to prune that
    company's stale listings this run (see db.close_stale_jobs)."""
    jobs: list[Job] = []
    results: dict[str, int | None] = {}
    for scraper_cls in all_scrapers():
        scraper = scraper_cls()
        try:
            company_jobs = link_health.filter_live_jobs(scraper.scrape())
            jobs.extend(company_jobs)
            results[scraper_cls.company_name] = len(company_jobs)
        except Exception:
            logger.exception("scraper %s failed", scraper_cls.company_name)
            results[scraper_cls.company_name] = None
    return jobs, results


def main() -> None:
    jobs, results = run_all()
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

        health_results = [scraper_health.evaluate(conn, company, count) for company, count in results.items()]

        for health in health_results:
            if health.should_skip_close:
                logger.warning(
                    "skipping close_stale_jobs for %s - %s detected, scraper likely broken",
                    health.company,
                    health.issue,
                )
                continue
            active_links = active_links_by_company.get(health.company, [])
            closed = db.close_stale_jobs(conn, health.company, active_links)
            if closed:
                logger.info("marked %d stale job(s) closed for %s", closed, health.company)

        newly_broken = [h for h in health_results if h.should_alert]
        if newly_broken:
            broken_companies = [h.company for h in newly_broken]
            logger.warning("%d scraper(s) newly flagged as broken: %s", len(newly_broken), broken_companies)
        alerts.send_email_summary(newly_broken)
        for health in health_results:
            if health.should_alert or health.is_recovery:
                alerts.file_or_close_issue(health)
    finally:
        conn.close()
