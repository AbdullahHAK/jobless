import html
import json
from datetime import date

from jobless.scrapers.safepay import SafepayScraper

JOB_POSTINGS = [
    {
        "id": 49974,
        "title": "Senior Backend Engineer",
        "url": "/companies/safepay/jobs/sYvXVJL-senior-backend-engineer",
        "applyUrl": "https://account.ycombinator.com/authenticate?continue=...",
        "location": "Karachi, Pakistan / Remote (US)",
        "skills": ["Python", "PostgreSQL"],
    },
    {
        "id": 50010,
        "title": "Growth Marketer",
        "url": "/companies/somecompany/jobs/abc-growth-marketer",
        "location": "San Francisco, CA",
        "skills": [],
    },
]


def test_scrape_keeps_only_pakistan_postings(mocker):
    # Build the escaped fixture the same way html.escape would encode a
    # real embedded JSON array, keyed as "jobPostings":[...].
    raw = '{"jobPostings":' + json.dumps(JOB_POSTINGS) + "}"
    page_html = f"<html><body><script>{html.escape(raw)}</script></body></html>"
    mock_get = mocker.patch("jobless.scrapers.safepay.requests.get")
    mock_get.return_value = mocker.Mock(text=page_html, raise_for_status=lambda: None)

    jobs = SafepayScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 1

    job = jobs[0]
    assert job.title == "Senior Backend Engineer"
    assert job.company == "Safepay"
    assert job.location == "Karachi, Pakistan / Remote (US)"
    assert str(job.apply_link) == "https://www.ycombinator.com/companies/safepay/jobs/sYvXVJL-senior-backend-engineer"
    assert job.date_scraped == date.today()


def test_scrape_returns_empty_list_when_no_job_postings_key(mocker):
    mock_get = mocker.patch("jobless.scrapers.safepay.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>no data here</body></html>", raise_for_status=lambda: None)

    jobs = SafepayScraper().scrape()

    assert jobs == []
