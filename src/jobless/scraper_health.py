import logging
from dataclasses import dataclass

from . import db

logger = logging.getLogger(__name__)

# A scraper that returns far fewer jobs than it last did almost always means
# its source changed shape (renamed JSON field, moved page, new selector)
# rather than the company genuinely closing nearly every opening overnight -
# closing "stale" jobs on a run like that would silently wipe out real,
# still-open postings (see runner.main / db.close_stale_jobs). Companies
# with a tiny board are exempt from the ratio check since e.g. 2 -> 0 is
# common and real there; MIN_BASELINE_FOR_RATIO_CHECK draws that line.
ANOMALY_DROP_RATIO = 0.2
MIN_BASELINE_FOR_RATIO_CHECK = 3

# An outright exception is never ambiguous, so it alerts on the very first
# occurrence. A silent drop in job count could just be one flaky scrape, so
# it waits for 2 consecutive anomalous runs before paging anyone - but the
# close_stale_jobs guard (should_skip_close) kicks in immediately either way,
# since wiping real data is the worse failure mode and costs nothing to avoid.
ALERT_THRESHOLD = {"exception": 1, "anomaly": 2}


@dataclass
class HealthResult:
    company: str
    issue: str | None  # "exception" | "anomaly" | None
    should_skip_close: bool
    should_alert: bool
    is_recovery: bool
    consecutive_issues: int
    job_count: int | None


def _is_anomalous(job_count: int, last_good_count: int) -> bool:
    if last_good_count == 0:
        return False  # no history yet, or this company is already known to have zero jobs
    if job_count == 0:
        return True
    if last_good_count >= MIN_BASELINE_FOR_RATIO_CHECK:
        return job_count <= last_good_count * ANOMALY_DROP_RATIO
    return False


def evaluate(conn, company: str, job_count: int | None) -> HealthResult:
    """Classifies this run's result for `company` against its scrape history
    and persists the updated health state. `job_count` is None when the
    scraper raised. The caller uses `should_skip_close` to decide whether
    it's safe to prune that company's stale listings this run, and
    `should_alert`/`is_recovery` to decide whether to notify."""
    previous = db.get_scraper_health(conn, company)
    last_good_count = previous["last_job_count"] if previous else 0
    prev_consecutive = previous["consecutive_issues"] if previous else 0
    was_broken = previous["is_broken"] if previous else False

    if job_count is None:
        issue = "exception"
    elif _is_anomalous(job_count, last_good_count):
        issue = "anomaly"
    else:
        issue = None

    if issue is None:
        db.upsert_scraper_health(
            conn, company, last_job_count=job_count, consecutive_issues=0, is_broken=False
        )
        return HealthResult(
            company=company,
            issue=None,
            should_skip_close=False,
            should_alert=False,
            is_recovery=was_broken,
            consecutive_issues=0,
            job_count=job_count,
        )

    consecutive = prev_consecutive + 1
    is_broken = consecutive >= ALERT_THRESHOLD[issue]
    db.upsert_scraper_health(
        conn,
        company,
        last_job_count=last_good_count,  # keep the last known-good count, not this run's bad reading
        consecutive_issues=consecutive,
        is_broken=is_broken,
    )
    return HealthResult(
        company=company,
        issue=issue,
        should_skip_close=True,
        should_alert=is_broken and not was_broken,
        is_recovery=False,
        consecutive_issues=consecutive,
        job_count=job_count,
    )
