from datetime import date

from jobless.scrapers.motive import MotiveScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Interested in joining our team?",
            "location": {"name": "Remote - Pakistan"},
            "absolute_url": "https://job-boards.greenhouse.io/gomotive/jobs/5476318002",
        },
        {
            "title": "Workplace Experience Coordinator",
            "location": {"name": "Pakistan - Lahore"},
            "absolute_url": "https://job-boards.greenhouse.io/gomotive/jobs/8745646002",
        },
        {
            "title": "Senior Software Engineer",
            "location": {"name": "United States - Remote"},
            "absolute_url": "https://job-boards.greenhouse.io/gomotive/jobs/9999999999",
        },
    ]
}


def test_scrape_excludes_catch_all_and_non_pakistan_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.motive.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = MotiveScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 1  # the catch-all and the US-only posting must both be excluded

    first = jobs[0]
    assert first.title == "Workplace Experience Coordinator"
    assert first.company == "Motive"
    assert first.location == "Pakistan - Lahore"
    assert str(first.apply_link) == "https://job-boards.greenhouse.io/gomotive/jobs/8745646002"
    assert first.date_scraped == date.today()


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.motive.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = MotiveScraper().scrape()

    assert jobs == []
