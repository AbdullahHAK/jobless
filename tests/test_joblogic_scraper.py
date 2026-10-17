from datetime import date

from jobless.scrapers.joblogic import JoblogicScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Senior Data Engineer",
            "location": {"name": "Lahore, Punjab, Pakistan"},
            "absolute_url": "https://job-boards.greenhouse.io/joblogic/jobs/1111111",
        },
        {
            "title": "Flutter Developer",
            "location": {"name": "Lahore, Punjab, Pakistan"},
            "absolute_url": "https://job-boards.greenhouse.io/joblogic/jobs/2222222",
        },
        {
            "title": "Senior Customer Success Manager, Strategic Accounts",
            "location": {"name": "Birmingham, England, United Kingdom"},
            "absolute_url": "https://job-boards.greenhouse.io/joblogic/jobs/3333333",
        },
    ]
}


def test_scrape_keeps_only_pakistan_tagged_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.joblogic.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = JoblogicScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the UK-only role is excluded

    first = jobs[0]
    assert first.title == "Senior Data Engineer"
    assert first.company == "Joblogic"
    assert first.location == "Lahore, Punjab, Pakistan"
    assert str(first.apply_link) == "https://job-boards.greenhouse.io/joblogic/jobs/1111111"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Flutter Developer"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.joblogic.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = JoblogicScraper().scrape()

    assert jobs == []
