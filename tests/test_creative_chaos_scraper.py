from datetime import date

from jobless.scrapers.creative_chaos import CreativeChaosScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Senior Software Engineer - Python",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/AAA1111111/apply",
        },
        {
            "title": "Digital Marketing Manager",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/BBB2222222/apply",
        },
        {
            "title": "Digital Marketing Manager",
            "city": "Karachi",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/BBB2222222/apply",
        },
        {
            "title": "Digital Marketing Manager",
            "city": "Islamabad",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/BBB2222222/apply",
        },
        {
            "title": "Principal AI Engineer",
            "city": "",
            "country": "India",
            "application_url": "https://apply.workable.com/j/CCC3333333/apply",
        },
        {
            "title": "Future Opportunities",
            "city": "",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/DDD4444444/apply",
        },
    ]
}


def test_scrape_merges_duplicate_city_rows_excludes_future_opportunities_and_non_pakistan(mocker):
    mock_get = mocker.patch("jobless.scrapers.creative_chaos.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = CreativeChaosScraper().scrape()

    assert mock_get.call_count == 1
    # The India-only role and the "Future Opportunities" catch-all are both excluded.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior Software Engineer - Python"
    assert first.company == "Creative Chaos"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://apply.workable.com/j/AAA1111111/apply"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Digital Marketing Manager"
    assert second.location == "Islamabad, Karachi, Lahore"  # 3 PK cities merged into one job


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.creative_chaos.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = CreativeChaosScraper().scrape()

    assert jobs == []
