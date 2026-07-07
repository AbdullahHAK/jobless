from datetime import date

from jobless.scrapers.devsinc import DevsincScraper

WIDGET_PAYLOAD = {
    "name": "Devsinc",
    "description": "<p>Devsinc helps startups, enterprises and public sector clients ...</p>",
    "jobs": [
        {
            "title": "Associate Software Engineer - OpenStack",
            "shortcode": "52AA5BD32C",
            "code": None,
            "employment_type": "Full-time",
            "telecommuting": False,
            "department": "Cluster Head",
            "url": "https://apply.workable.com/j/52AA5BD32C",
            "shortlink": "https://apply.workable.com/j/52AA5BD32C",
            "application_url": "https://apply.workable.com/j/52AA5BD32C/apply",
            "published_on": "2026-06-29",
            "created_at": "2026-06-15",
            "country": "Pakistan",
            "city": "Lahore",
            "state": "Punjab",
            "education": "Bachelor's Degree",
            "experience": "Associate",
            "function": "Engineering",
            "industry": "",
            "locations": [
                {
                    "country": "Pakistan",
                    "countryCode": "PK",
                    "city": "Lahore",
                    "region": "Punjab",
                    "hidden": False,
                }
            ],
        },
        {
            "title": "Associate Business Development Executive",
            "shortcode": "9075A1EA1B",
            "code": None,
            "employment_type": "Full-time",
            "telecommuting": True,
            "department": "Global B2B Sales and Business Development",
            "url": "https://apply.workable.com/j/9075A1EA1B",
            "shortlink": "https://apply.workable.com/j/9075A1EA1B",
            "application_url": "https://apply.workable.com/j/9075A1EA1B/apply",
            "published_on": "2026-01-15",
            "created_at": "2026-01-15",
            "country": "Saudi Arabia",
            "city": "",
            "state": "",
            "education": None,
            "experience": "Associate",
            "function": None,
            "industry": None,
            "locations": [
                {
                    "country": "Saudi Arabia",
                    "countryCode": "SA",
                    "city": None,
                    "region": None,
                    "hidden": False,
                }
            ],
        },
    ],
}


def test_scrape_builds_job_schema_from_workable_widget(mocker):
    mock_get = mocker.patch("jobless.scrapers.devsinc.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: WIDGET_PAYLOAD, raise_for_status=lambda: None)

    jobs = DevsincScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Associate Software Engineer - OpenStack"
    assert first.company == "Devsinc"
    assert first.location == "Lahore, Pakistan"
    assert str(first.apply_link) == "https://apply.workable.com/j/52AA5BD32C"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Associate Business Development Executive"
    assert second.location == "Saudi Arabia"
    assert str(second.apply_link) == "https://apply.workable.com/j/9075A1EA1B"
