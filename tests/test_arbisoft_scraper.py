from datetime import date

from jobless.scrapers.arbisoft import ArbisoftScraper

PAGE_ONE = {
    "count": 2,
    "next": "https://arbisoft.hirestream.io/api/v1/jobs/published-jobs/?limit=1&offset=1",
    "previous": None,
    "results": [
        {
            "id": 1,
            "uuid": "11111111-1111-1111-1111-111111111111",
            "title": "Senior Software Engineer",
            "department": "Software Engineering",
            "location": "Lahore",
            "positions": 1,
        }
    ],
}

PAGE_TWO = {
    "count": 2,
    "next": None,
    "previous": PAGE_ONE["next"],
    "results": [
        {
            "id": 2,
            "uuid": "22222222-2222-2222-2222-222222222222",
            "title": "QA Engineer",
            "department": "Software Quality Assurance",
            "location": "Islamabad",
            "positions": 2,
        }
    ],
}


def test_scrape_follows_pagination_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.arbisoft.requests.get")
    mock_get.side_effect = [
        mocker.Mock(json=lambda: PAGE_ONE, raise_for_status=lambda: None),
        mocker.Mock(json=lambda: PAGE_TWO, raise_for_status=lambda: None),
    ]
    mocker.patch("jobless.scrapers.arbisoft.time.sleep")

    jobs = ArbisoftScraper().scrape()

    assert mock_get.call_count == 2
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior Software Engineer"
    assert first.company == "Arbisoft"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://arbisoft.hirestream.io/job/view-job/11111111-1111-1111-1111-111111111111/"
    assert first.date_scraped == date.today()

    assert jobs[1].title == "QA Engineer"
