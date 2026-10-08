from datetime import date

from jobless.scrapers.inbox_business_technologies import InboxBusinessTechnologiesScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Junior Oracle DBA",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/AAA1111111/apply",
        },
        {
            "title": "Technical Support Officer",
            "city": "Islamabad",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/BBB2222222/apply",
        },
        {
            "title": "Technical Support Officer",
            "city": "Karachi",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/CCC3333333/apply",
        },
        {
            "title": "Data Governance Analyst",
            "city": "Riyadh",
            "country": "Saudi Arabia",
            "application_url": "https://apply.workable.com/j/DDD4444444/apply",
        },
    ]
}


def test_scrape_filters_to_pakistan_and_keeps_distinct_same_title_postings_separate(mocker):
    mock_get = mocker.patch("jobless.scrapers.inbox_business_technologies.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = InboxBusinessTechnologiesScraper().scrape()

    assert mock_get.call_count == 1
    # The Saudi Arabia-only role is excluded; the two "Technical Support
    # Officer" postings have distinct application_urls, so they must stay
    # as two separate jobs, not get merged into one.
    assert len(jobs) == 3

    first = jobs[0]
    assert first.title == "Junior Oracle DBA"
    assert first.company == "Inbox Business Technologies"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://apply.workable.com/j/AAA1111111/apply"
    assert first.date_scraped == date.today()

    titles_and_locations = {(j.title, j.location) for j in jobs}
    assert ("Technical Support Officer", "Islamabad") in titles_and_locations
    assert ("Technical Support Officer", "Karachi") in titles_and_locations


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.inbox_business_technologies.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = InboxBusinessTechnologiesScraper().scrape()

    assert jobs == []
