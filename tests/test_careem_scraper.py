from datetime import date

from jobless.scrapers.careem import CareemScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Associate Director of Ads Sales",
            "location": {"name": "Dubai, United Arab Emirates"},
            "absolute_url": "https://boards.greenhouse.io/careem/jobs/8618945002",
        },
        {
            "title": "Senior Software Engineer I",
            "location": {"name": "Karachi, Pakistan; Lahore, Pakistan"},
            "absolute_url": "https://boards.greenhouse.io/careem/jobs/8131791002",
        },
        {
            "title": "Senior Software Engineer I - Backend",
            "location": {"name": "Amman, Jordan; Islamabad, Pakistan; Karachi, Pakistan"},
            "absolute_url": "https://boards.greenhouse.io/careem/jobs/8620291002",
        },
    ]
}


def test_scrape_keeps_only_postings_mentioning_pakistan(mocker):
    mock_get = mocker.patch("jobless.scrapers.careem.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = CareemScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the Dubai-only posting must be excluded

    first = jobs[0]
    assert first.title == "Senior Software Engineer I"
    assert first.company == "Careem"
    assert first.location == "Karachi, Pakistan; Lahore, Pakistan"
    assert str(first.apply_link) == "https://boards.greenhouse.io/careem/jobs/8131791002"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior Software Engineer I - Backend"
    assert second.location == "Amman, Jordan; Islamabad, Pakistan; Karachi, Pakistan"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.careem.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = CareemScraper().scrape()

    assert jobs == []
