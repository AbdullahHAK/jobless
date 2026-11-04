from datetime import date

from jobless.scrapers.jazz import JazzScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Penetration Tester - TPL Insurance",
            "city": "Karachi",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/8B2D757E33/apply",
        },
        {
            "title": "Lead Solution Architect - Digital, AI & Fintech Solutions",
            "city": "Islamabad",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/F37876ECA5/apply",
        },
        {
            "title": "Lead Solution Architect - Digital, AI & Fintech Solutions",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/F37876ECA5/apply",
        },
        {
            "title": "Some Global Role",
            "city": "Dubai",
            "country": "United Arab Emirates",
            "application_url": "https://apply.workable.com/j/AAAAAAAAAA/apply",
        },
    ]
}


def test_scrape_merges_duplicate_city_rows_and_drops_non_pakistan_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.jazz.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = JazzScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the UAE-only job must be excluded

    first = jobs[0]
    assert first.title == "Penetration Tester - TPL Insurance"
    assert first.company == "Jazz"
    assert first.location == "Karachi"
    assert str(first.apply_link) == "https://apply.workable.com/j/8B2D757E33/apply"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Lead Solution Architect - Digital, AI & Fintech Solutions"
    assert second.location == "Islamabad, Lahore"  # both PK cities merged into one job, not duplicated


def test_scrape_falls_back_to_pakistan_when_city_is_blank(mocker):
    payload = {
        "jobs": [
            {
                "title": "Strategy Analyst",
                "city": "",
                "country": "Pakistan",
                "application_url": "https://apply.workable.com/j/BBBBBBBBBB/apply",
            }
        ]
    }
    mock_get = mocker.patch("jobless.scrapers.jazz.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: payload, raise_for_status=lambda: None)

    jobs = JazzScraper().scrape()

    assert jobs[0].location == "Pakistan"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.jazz.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = JazzScraper().scrape()

    assert jobs == []
