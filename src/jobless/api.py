from collections.abc import Generator
from datetime import date, datetime
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, EmailStr

from . import db

app = FastAPI(title="Jobless API")

# /jobs, /companies, /health, and /subscribe are all public, credential-free
# endpoints over non-sensitive data - there's nothing a wildcard origin
# exposes here that isn't already public, so this stays simple rather than
# maintaining an allowlist of frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
)

# Exposes GET /metrics in Prometheus text format (request counts, latency
# histograms, in-progress requests, per path+status). Once kube-prometheus-
# stack is installed in-cluster, a ServiceMonitor selecting the jobless-api
# Service is all that's needed to start scraping this - no code changes.
Instrumentator().instrument(app).expose(app)


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    apply_link: str
    date_scraped: date
    first_seen_at: datetime


class SubscribeRequest(BaseModel):
    name: str
    email: EmailStr
    frequency: Literal["daily", "weekly"]


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


@app.get("/companies", response_model=list[str])
def get_companies(conn: psycopg.Connection = Depends(get_db_connection)) -> list[str]:
    return db.list_companies(conn)


@app.get("/jobs", response_model=list[JobOut])
def get_jobs(
    company: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: psycopg.Connection = Depends(get_db_connection),
) -> list[dict]:
    return db.list_jobs(conn, company=company, limit=limit, offset=offset)


@app.post("/subscribe")
def subscribe(
    body: SubscribeRequest,
    conn: psycopg.Connection = Depends(get_db_connection),
) -> dict:
    db.add_subscriber(conn, name=body.name, email=body.email, frequency=body.frequency)
    return {"status": "subscribed"}


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(token: str, conn: psycopg.Connection = Depends(get_db_connection)) -> str:
    if not db.remove_subscriber(conn, token):
        raise HTTPException(status_code=404, detail="Subscription not found - it may already be removed.")
    return "<html><body><p>You've been unsubscribed. Sorry to see you go.</p></body></html>"
