from datetime import date

from jobless.scrapers.remotebase import RemotebaseScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "AI Engineer",
            "city": "",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/6E7795E82F/apply",
        },
        {
            "title": "Founding Engineer, AI Platform",
            "city": "",
            "country": "United States",
            "application_url": "https://apply.workable.com/j/943EA3801F/apply",
        },
        {
            "title": "React Native Developer",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/EA21727854/apply",
        },
    ]
}


def test_scrape_keeps_only_pakistan_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.remotebase.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = RemotebaseScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the United States posting must be excluded

    first = jobs[0]
    assert first.title == "AI Engineer"
    assert first.company == "Remotebase"
    assert first.location == "Not specified"  # blank city falls back cleanly
    assert str(first.apply_link) == "https://apply.workable.com/j/6E7795E82F/apply"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "React Native Developer"
    assert second.location == "Lahore"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.remotebase.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = RemotebaseScraper().scrape()

    assert jobs == []
