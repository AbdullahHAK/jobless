import logging
import os

import psycopg

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
"""

# apply_link is the natural dedup key: it's the one field every scraper
# produces that's actually unique per posting. Re-scraping a still-open job
# just refreshes its title/location/date_scraped in place instead of adding
# a duplicate row; first_seen_at is only set on the initial insert.
_UPSERT = """
INSERT INTO jobs (title, company, location, apply_link, date_scraped)
VALUES (%(title)s, %(company)s, %(location)s, %(apply_link)s, %(date_scraped)s)
ON CONFLICT (apply_link) DO UPDATE SET
    title = EXCLUDED.title,
    company = EXCLUDED.company,
    location = EXCLUDED.location,
    date_scraped = EXCLUDED.date_scraped;
"""


def get_connection() -> psycopg.Connection:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return psycopg.connect(database_url)


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
