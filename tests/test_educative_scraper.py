from datetime import date

from jobless.scrapers.educative import EducativeScraper

JOBS_PAYLOAD = [
    {
        "text": "Software Engineer (Experienced)",
        "country": "PK",
        "categories": {"location": "Lahore"},
        "hostedUrl": "https://jobs.lever.co/educative/aaa11111",
    },
    {
        "text": "Senior Technical Content Engineers (Islamabad)",
        "country": "PK",
        "categories": {"location": "Islamabad"},
        "hostedUrl": "https://jobs.lever.co/educative/bbb22222",
    },
    {
        "text": "Director of Finance and Operations",
        "country": "US",
        "categories": {"location": "Bellevue, WA"},
        "hostedUrl": "https://jobs.lever.co/educative/ccc33333",
    },
]


def test_scrape_keeps_only_pk_country_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.educative.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = EducativeScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the US-based role is excluded

    first = jobs[0]
    assert first.title == "Software Engineer (Experienced)"
    assert first.company == "Educative"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://jobs.lever.co/educative/aaa11111"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior Technical Content Engineers (Islamabad)"
    assert second.location == "Islamabad"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.educative.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: [], raise_for_status=lambda: None)

    jobs = EducativeScraper().scrape()

    assert jobs == []
