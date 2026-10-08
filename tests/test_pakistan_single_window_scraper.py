from datetime import date

from jobless.scrapers.pakistan_single_window import PakistanSingleWindowScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "SVP - Enterprise Data, Business Intelligence & Analytics",
            "city": "Karachi",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/AAA1111111/apply",
        },
        {
            "title": "Systems Engineer - IT Support",
            "city": "Islamabad",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/BBB2222222/apply",
        },
        {
            "title": "Regional Consultant",
            "city": "Dubai",
            "country": "United Arab Emirates",
            "application_url": "https://apply.workable.com/j/CCC3333333/apply",
        },
    ]
}


def test_scrape_filters_to_pakistan_postings_only(mocker):
    mock_get = mocker.patch("jobless.scrapers.pakistan_single_window.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = PakistanSingleWindowScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the UAE-only role is excluded

    first = jobs[0]
    assert first.title == "SVP - Enterprise Data, Business Intelligence & Analytics"
    assert first.company == "Pakistan Single Window"
    assert first.location == "Karachi"
    assert str(first.apply_link) == "https://apply.workable.com/j/AAA1111111/apply"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Systems Engineer - IT Support"
    assert second.location == "Islamabad"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.pakistan_single_window.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = PakistanSingleWindowScraper().scrape()

    assert jobs == []
