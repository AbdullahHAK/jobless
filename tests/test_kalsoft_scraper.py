from datetime import date

from jobless.scrapers.kalsoft import KalSoftScraper

JOBS_PAYLOAD = {
    "count": 3,
    "jobs": [
        {
            "Id": "22f30ce1-cd33-44f9-83d4-b1022f82dc66",
            "name": "Sales Development Representative (SDR)",
            "location": "Canada (Remote/Hybrid)",
            "isClosed": False,
            "experience": "1-3 Years",
        },
        {
            "Id": "ac43531a-6045-4e54-91f8-2dd53b421b2c",
            "name": "Tier 3 Senior Cloud & Security Architect",
            "location": "Canada / Kuwait",
            "isClosed": False,
            "experience": "5+ Years",
        },
        {
            "Id": "closed-job-id-0000",
            "name": "Old Closed Role",
            "location": "Lahore",
            "isClosed": True,
            "experience": "2 Years",
        },
    ],
}


def test_scrape_filters_closed_jobs_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.kalsoft.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = KalSoftScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the closed role must be excluded

    first = jobs[0]
    assert first.title == "Sales Development Representative (SDR)"
    assert first.company == "KalSoft"
    assert first.location == "Canada (Remote/Hybrid)"
    assert str(first.apply_link) == "https://www.kalsoft.com/careers/?job=22f30ce1-cd33-44f9-83d4-b1022f82dc66"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Tier 3 Senior Cloud & Security Architect"
    assert second.location == "Canada / Kuwait"


def test_scrape_returns_empty_list_when_no_jobs_key(mocker):
    mock_get = mocker.patch("jobless.scrapers.kalsoft.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"count": 0, "jobs": []}, raise_for_status=lambda: None)

    jobs = KalSoftScraper().scrape()

    assert jobs == []
