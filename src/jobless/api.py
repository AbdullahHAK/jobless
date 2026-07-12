from collections.abc import Generator
from datetime import date, datetime

import psycopg
from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel

from . import db

app = FastAPI(title="Jobless API")


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    apply_link: str
    date_scraped: date
    first_seen_at: datetime


def get_db_connection() -> Generator[psycopg.Connection]:
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health(conn: psycopg.Connection = Depends(get_db_connection)) -> dict:
    conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/jobs", response_model=list[JobOut])
def get_jobs(
    company: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: psycopg.Connection = Depends(get_db_connection),
) -> list[dict]:
    return db.list_jobs(conn, company=company, limit=limit, offset=offset)
