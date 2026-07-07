from datetime import date

from jobless.scrapers.ten_pearls import TenPearlsScraper

JOBS_PAYLOAD = [
    {
        "id": "job_20260706105912_TWVHOVPBBR7HTP8P",
        "title": "Product Manager (AI Products) - Morning/Afternoon Shift",
        "country_id": "Pakistan",
        "city": "Karachi, Islamabad",
        "state": "Karachi, Islamabad",
        "zip": "",
        "department": "",
        "description": "<p>Company overview and role details...</p>",
        "minimum_salary": None,
        "maximum_salary": None,
        "notes": "",
        "original_open_date": "2026-07-06",
        "type": "Full Time",
        "status": "Open",
        "send_to_job_boards": True,
        "hiring_lead": "Jane Doe",
        "board_code": "eYaJRx6Uhq",
        "internal_code": "",
        "questionnaire": None,
        "workflow_id": "123",
        "minimum_public_salary": None,
        "maximum_public_salary": None,
    },
    {
        "id": "job_20260701090000_ABCDEFGHIJKLMNOP",
        "title": "Senior QA Automation Engineer",
        "country_id": "Pakistan",
        "city": "Lahore",
        "state": "",
        "zip": "",
        "department": "Quality Assurance",
        "description": "<p>Another role description</p>",
        "minimum_salary": None,
        "maximum_salary": None,
        "notes": "",
        "original_open_date": "2026-07-01",
        "type": "Full Time",
        "status": "Open",
        "send_to_job_boards": True,
        "hiring_lead": "John Roe",
        "board_code": "C5CvZBqAzJ",
        "internal_code": "",
        "questionnaire": None,
        "workflow_id": "124",
        "minimum_public_salary": None,
        "maximum_public_salary": None,
    },
    {
        "id": "job_20260628000000_DRAFTDRAFTDRAFT1",
        "title": "Unpublished Draft Role",
        "country_id": "Pakistan",
        "city": "Karachi",
        "state": "",
        "zip": "",
        "department": "",
        "description": "",
        "minimum_salary": None,
        "maximum_salary": None,
        "notes": "",
        "original_open_date": "2026-06-28",
        "type": "Full Time",
        "status": "Drafting",
        "send_to_job_boards": False,
        "hiring_lead": "",
        "board_code": "",
        "internal_code": "",
        "questionnaire": None,
        "workflow_id": "125",
        "minimum_public_salary": None,
        "maximum_public_salary": None,
    },
]


def test_scrape_filters_open_jobs_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.ten_pearls.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = TenPearlsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the "Drafting" (unpublished) job must be excluded

    first = jobs[0]
    assert first.title == "Product Manager (AI Products) - Morning/Afternoon Shift"
    assert first.company == "10Pearls"
    assert first.location == "Karachi, Islamabad"
    assert (
        str(first.apply_link)
        == "https://10pearls.applytojob.com/apply/jobs/details/job_20260706105912_TWVHOVPBBR7HTP8P"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior QA Automation Engineer"
    assert second.location == "Lahore"
