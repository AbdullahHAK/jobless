import logging
import os

import requests

from . import digest
from .scraper_health import HealthResult

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 10

# Every issue this files carries this label, which doubles as how it finds
# the still-open issue to close again on recovery (see _find_open_issue).
ISSUE_LABEL = "scraper-broken"

ISSUE_DESCRIPTIONS = {
    "exception": "is raising an exception instead of returning jobs",
    "anomaly": "returned a suspiciously low job count compared to its last known-good run",
}


def _issue_title(company: str) -> str:
    return f"Scraper broken: {company}"


def _run_url() -> str | None:
    # Only set inside GitHub Actions - gives the alert a direct link back to
    # the run that caught the problem, with the full scraper log attached.
    env_vars = ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")
    server, repo, run_id = (os.environ.get(v) for v in env_vars)
    if not (server and repo and run_id):
        return None
    return f"{server}/{repo}/actions/runs/{run_id}"


def _github_headers() -> dict[str, str] | None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def _find_open_issue(repo: str, headers: dict[str, str], company: str) -> dict | None:
    response = requests.get(
        f"{GITHUB_API_URL}/repos/{repo}/issues",
        headers=headers,
        params={"state": "open", "labels": ISSUE_LABEL},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return next((issue for issue in response.json() if issue["title"] == _issue_title(company)), None)


def file_or_close_issue(result: HealthResult) -> None:
    """Files a labeled issue the first time a company's scraper is flagged
    broken, and closes it again the first run it recovers. Deliberately
    skipped entirely when GITHUB_TOKEN/GITHUB_REPOSITORY aren't set (e.g.
    local runs) rather than failing - this is a notification, not a
    requirement for the scrape itself to succeed."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    headers = _github_headers()
    if not repo or headers is None:
        return

    try:
        existing = _find_open_issue(repo, headers, result.company)

        if result.is_recovery:
            if existing:
                requests.patch(
                    f"{GITHUB_API_URL}/repos/{repo}/issues/{existing['number']}",
                    headers=headers,
                    json={"state": "closed"},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                ).raise_for_status()
            return

        if result.should_alert and existing is None:
            run_url = _run_url()
            body = (
                f"`{result.company}`'s scraper {ISSUE_DESCRIPTIONS[result.issue]} "
                f"({result.consecutive_issues} consecutive run(s) as of this one).\n\n"
                "Likely cause: the company's career page or API changed shape. Its stale "
                "listings are being kept as-is (not pruned) until the scraper is fixed, so "
                "no real data has been lost.\n\n"
                + (f"[Scrape run that caught this]({run_url})\n\n" if run_url else "")
                + "This issue closes itself automatically once the scraper reports a normal run."
            )
            requests.post(
                f"{GITHUB_API_URL}/repos/{repo}/issues",
                headers=headers,
                json={"title": _issue_title(result.company), "body": body, "labels": [ISSUE_LABEL]},
                timeout=REQUEST_TIMEOUT_SECONDS,
            ).raise_for_status()
    except requests.RequestException:
        logger.exception("failed to file/close GitHub issue for %s", result.company)


def send_email_summary(broken: list[HealthResult]) -> None:
    """One summary email for every newly-broken company this run, reusing
    the existing Resend wiring from digest.py. No-ops if ALERT_EMAIL isn't
    configured or nothing newly broke - deliberately silent on recovery and
    on already-known-broken companies, so this doesn't become daily noise."""
    alert_email = os.environ.get("ALERT_EMAIL")
    if not alert_email or not broken or "RESEND_API_KEY" not in os.environ:
        return

    run_url = _run_url()
    items = "".join(
        f"<li><strong>{r.company}</strong> &mdash; {ISSUE_DESCRIPTIONS[r.issue]}</li>" for r in broken
    )
    html = (
        f"<html><body><h2>Jobless: {len(broken)} scraper(s) look broken</h2>"
        f"<ul>{items}</ul>"
        "<p>Their listings are being kept as-is, not pruned, until each scraper is fixed.</p>"
        + (f'<p><a href="{run_url}">View the scrape run</a></p>' if run_url else "")
        + "</body></html>"
    )

    try:
        digest.send_email(alert_email, f"Jobless: {len(broken)} scraper(s) need attention", html)
    except requests.RequestException:
        logger.exception("failed to send scraper-health alert email")
