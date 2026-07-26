import argparse
import logging
import os
from datetime import UTC, datetime, timedelta

import requests

from . import db

logger = logging.getLogger(__name__)

WINDOWS = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}

RESEND_API_URL = "https://api.resend.com/emails"
REQUEST_TIMEOUT_SECONDS = 10

# onboarding@resend.dev is Resend's shared sandbox sender - works with zero
# setup but (per Resend's own docs) can only deliver to the account owner's
# own verified address until a custom domain is verified. Fine for testing
# this end-to-end; switch to a verified domain's address before relying on
# this to actually reach subscribers.
DEFAULT_FROM_EMAIL = "onboarding@resend.dev"


def _job_html(job: dict) -> str:
    return (
        f'<li><a href="{job["apply_link"]}">{job["title"]}</a>'
        f" &mdash; {job['company']} &middot; {job['location']}</li>"
    )


def render_email_html(jobs: list[dict], unsubscribe_url: str) -> str:
    items = "\n".join(_job_html(job) for job in jobs)
    return f"""
    <html><body>
      <h2>New jobs on Jobless</h2>
      <ul>{items}</ul>
      <p style="color:#666;font-size:12px;">
        <a href="{unsubscribe_url}">Unsubscribe</a>
      </p>
    </body></html>
    """.strip()


def send_email(to_email: str, subject: str, html: str) -> None:
    api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ.get("RESEND_FROM_EMAIL", DEFAULT_FROM_EMAIL)

    response = requests.post(
        RESEND_API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"from": from_email, "to": [to_email], "subject": subject, "html": html},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def run(frequency: str) -> None:
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    since = datetime.now(UTC) - WINDOWS[frequency]

    conn = db.get_connection()
    try:
        jobs = db.list_new_jobs(conn, since)
        if not jobs:
            logger.info("no new jobs since %s, skipping %s digest", since, frequency)
            return

        subscribers = db.list_subscribers(conn, frequency)
        logger.info(
            "sending %s digest (%d new jobs) to %d subscriber(s)", frequency, len(jobs), len(subscribers)
        )

        sent = 0
        for subscriber in subscribers:
            unsubscribe_url = f"{api_base_url}/unsubscribe?token={subscriber['unsubscribe_token']}"
            html = render_email_html(jobs, unsubscribe_url)
            try:
                send_email(subscriber["email"], f"{len(jobs)} new job(s) on Jobless", html)
                sent += 1
            except requests.RequestException:
                logger.exception("failed to send %s digest to subscriber %d", frequency, subscriber["id"])

        logger.info("sent %d/%d %s digest email(s)", sent, len(subscribers), frequency)
    finally:
        conn.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("frequency", choices=["daily", "weekly"])
    args = parser.parse_args()
    run(args.frequency)


if __name__ == "__main__":
    main()
