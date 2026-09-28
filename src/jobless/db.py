import logging
import os
import secrets
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from .scrapers.base import Job

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "postgresql://jobless:jobless@localhost:5432/jobless"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    apply_link TEXT NOT NULL UNIQUE,
    date_scraped DATE NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- CREATE TABLE IF NOT EXISTS is a no-op once the table already exists (e.g.
-- on the live Neon DB), so a new column needs its own idempotent statement
-- to actually reach an existing deployment.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

CREATE TABLE IF NOT EXISTS subscribers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly')),
    unsubscribe_token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- is_approved defaults false: a submitted review is invisible to the
-- public (see list_reviews) until a moderator approves it via
-- approve_review. Hosting unmoderated claims/ratings about real companies
-- carries real spam and defamation-risk exposure, unlike jobs/subscribers
-- which are either scraped facts or private to the subscriber themselves.
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    role TEXT,
    employment_status TEXT NOT NULL CHECK (employment_status IN ('current', 'former')),
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    salary_range TEXT,
    review_text TEXT NOT NULL,
    is_approved BOOLEAN NOT NULL DEFAULT false,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

# apply_link is the natural dedup key: it's the one field every scraper
# produces that's actually unique per posting. Re-scraping a still-open job
# just refreshes its title/location/date_scraped in place instead of adding
# a duplicate row; first_seen_at is only set on the initial insert.
# is_active is forced true here too, so a job that closed (see
# close_stale_jobs) and later reopens under the same apply_link comes back
# instead of staying hidden forever.
_UPSERT = """
INSERT INTO jobs (title, company, location, apply_link, date_scraped, is_active)
VALUES (%(title)s, %(company)s, %(location)s, %(apply_link)s, %(date_scraped)s, true)
ON CONFLICT (apply_link) DO UPDATE SET
    title = EXCLUDED.title,
    company = EXCLUDED.company,
    location = EXCLUDED.location,
    date_scraped = EXCLUDED.date_scraped,
    is_active = true;
"""


CONNECT_TIMEOUT_SECONDS = 5


def get_connection() -> psycopg.Connection:
    # Without an explicit timeout, a DB outage can hang a connecting client
    # indefinitely instead of failing fast - found by actually testing this
    # (started the API with no Postgres reachable; a request to /jobs just
    # hung rather than erroring). That defeats the point of readiness/
    # liveness probes and piles up stuck requests under real load.
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return psycopg.connect(database_url, connect_timeout=CONNECT_TIMEOUT_SECONDS)


def init_db(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(_SCHEMA)
    conn.commit()


def save_jobs(conn: psycopg.Connection, jobs: list[Job]) -> int:
    """Upsert jobs by apply_link. Returns the number of jobs processed."""
    if not jobs:
        return 0

    rows = [
        {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "apply_link": str(job.apply_link),
            "date_scraped": job.date_scraped,
        }
        for job in jobs
    ]

    with conn.cursor() as cur:
        cur.executemany(_UPSERT, rows)
    conn.commit()

    logger.info("saved %d jobs to the database", len(rows))
    return len(rows)


def close_stale_jobs(conn: psycopg.Connection, company: str, active_apply_links: list[str]) -> int:
    """Mark a company's jobs inactive if they're currently active but weren't
    in its latest successful scrape - i.e. the posting was closed/removed on
    the company's own site. Scoped to one company and only meant to be
    called for a company whose scraper actually succeeded this run - a
    scraper that failed and returned nothing must never be treated as "this
    company now has zero open jobs," or a transient site/network hiccup
    would silently wipe out every real listing for that company."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET is_active = false
            WHERE company = %(company)s
              AND is_active = true
              AND apply_link != ALL(%(active_links)s);
            """,
            {"company": company, "active_links": active_apply_links},
        )
        closed = cur.rowcount
    conn.commit()
    return closed


def list_jobs(
    conn: psycopg.Connection,
    company: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Return active jobs, most recently scraped first, optionally filtered by company."""
    query = (
        "SELECT id, title, company, location, apply_link, date_scraped, first_seen_at "
        "FROM jobs WHERE is_active = true"
    )
    params: dict = {"limit": limit, "offset": offset}
    if company:
        query += " AND company = %(company)s"
        params["company"] = company
    query += " ORDER BY date_scraped DESC, id DESC LIMIT %(limit)s OFFSET %(offset)s;"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def list_all_jobs(conn: psycopg.Connection) -> list[dict]:
    """Every active job, unpaginated - for the static site export, which
    ships the whole dataset as one JSON file rather than paginating over an
    API."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, title, company, location, apply_link, date_scraped, first_seen_at "
            "FROM jobs WHERE is_active = true ORDER BY date_scraped DESC, id DESC;"
        )
        return cur.fetchall()


def list_new_jobs(conn: psycopg.Connection, since: datetime) -> list[dict]:
    """Active jobs first seen at or after `since` - for email digests,
    deliberately keyed on first_seen_at rather than date_scraped so a still-
    open job that gets re-scraped every day doesn't get resent to
    subscribers every day."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, title, company, location, apply_link, first_seen_at
            FROM jobs
            WHERE first_seen_at >= %(since)s AND is_active = true
            ORDER BY first_seen_at DESC;
            """,
            {"since": since},
        )
        return cur.fetchall()


def list_companies(conn: psycopg.Connection) -> list[str]:
    """Distinct companies that currently have at least one active job."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT company FROM jobs WHERE is_active = true ORDER BY company;")
        return [row[0] for row in cur.fetchall()]


# Upsert by email: resubmitting the signup form (e.g. to switch daily <->
# weekly) updates name/frequency in place rather than erroring on the unique
# email constraint. unsubscribe_token is deliberately left out of the
# DO UPDATE SET clause so an existing subscriber's unsubscribe link - already
# possibly sitting in an old email - keeps working rather than silently
# breaking on their next resubmit.
_ADD_SUBSCRIBER = """
INSERT INTO subscribers (name, email, frequency, unsubscribe_token)
VALUES (%(name)s, %(email)s, %(frequency)s, %(token)s)
ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    frequency = EXCLUDED.frequency
RETURNING unsubscribe_token;
"""


def add_subscriber(conn: psycopg.Connection, name: str, email: str, frequency: str) -> str:
    """Insert or update a subscriber. Returns their unsubscribe token."""
    params = {
        "name": name,
        "email": email,
        "frequency": frequency,
        "token": secrets.token_urlsafe(32),
    }
    with conn.cursor() as cur:
        cur.execute(_ADD_SUBSCRIBER, params)
        token = cur.fetchone()[0]
    conn.commit()
    return token


def remove_subscriber(conn: psycopg.Connection, token: str) -> bool:
    """Delete a subscriber by their unsubscribe token. Returns whether one was found."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM subscribers WHERE unsubscribe_token = %(token)s;", {"token": token})
        removed = cur.rowcount > 0
    conn.commit()
    return removed


def list_subscribers(conn: psycopg.Connection, frequency: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, name, email, unsubscribe_token FROM subscribers WHERE frequency = %(frequency)s;",
            {"frequency": frequency},
        )
        return cur.fetchall()


def add_review(
    conn: psycopg.Connection,
    company: str,
    employment_status: str,
    rating: int,
    review_text: str,
    role: str | None = None,
    salary_range: str | None = None,
) -> int:
    """Insert a new review as unapproved. Returns the new row's id -
    callers should tell submitters it's pending moderation, not live yet."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO reviews (company, role, employment_status, rating, salary_range, review_text)
            VALUES (
                %(company)s, %(role)s, %(employment_status)s, %(rating)s, %(salary_range)s, %(review_text)s
            )
            RETURNING id;
            """,
            {
                "company": company,
                "role": role,
                "employment_status": employment_status,
                "rating": rating,
                "salary_range": salary_range,
                "review_text": review_text,
            },
        )
        review_id = cur.fetchone()[0]
    conn.commit()
    return review_id


def list_reviews(conn: psycopg.Connection, company: str | None = None) -> list[dict]:
    """Approved reviews only, most recent first - see add_review/approve_review
    for why unapproved submissions never reach this query."""
    query = (
        "SELECT id, company, role, employment_status, rating, salary_range, review_text, submitted_at "
        "FROM reviews WHERE is_approved = true"
    )
    params: dict = {}
    if company:
        query += " AND company = %(company)s"
        params["company"] = company
    query += " ORDER BY submitted_at DESC;"

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def list_pending_reviews(conn: psycopg.Connection) -> list[dict]:
    """Unapproved submissions awaiting moderation - admin-only, oldest first
    so a moderator works through the backlog in submission order."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT id, company, role, employment_status, rating, salary_range, review_text, submitted_at "
            "FROM reviews WHERE is_approved = false ORDER BY submitted_at ASC;"
        )
        return cur.fetchall()


def approve_review(conn: psycopg.Connection, review_id: int) -> bool:
    """Mark a pending review approved, making it publicly visible via
    list_reviews. Returns whether a matching pending review was found."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE reviews SET is_approved = true WHERE id = %(id)s AND is_approved = false;",
            {"id": review_id},
        )
        approved = cur.rowcount > 0
    conn.commit()
    return approved


def reject_review(conn: psycopg.Connection, review_id: int) -> bool:
    """Delete a pending review a moderator rejected (spam/fake/abusive) -
    rejected submissions aren't worth soft-deleting like closed jobs, there's
    no future use for keeping them around. Returns whether one was found."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM reviews WHERE id = %(id)s AND is_approved = false;",
            {"id": review_id},
        )
        rejected = cur.rowcount > 0
    conn.commit()
    return rejected
