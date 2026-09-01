from datetime import date

from jobless.scrapers.prime_system_solutions import PrimeSystemSolutionsScraper

JOBS_PAYLOAD = {
    "jobs": [
        {
            "title": "Trainee Engineer (Internship to Hire Program)",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/26B0160E9A/apply",
        },
        {
            "title": "System & Network Engineer (Level II)",
            "city": "Lahore",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/87EFD22561/apply",
        },
        {
            "title": "System & Network Engineer (Level II)",
            "city": "Islamabad",
            "country": "Pakistan",
            "application_url": "https://apply.workable.com/j/87EFD22561/apply",
        },
        {
            "title": "Systems Engineer (Level II)",
            "city": "Johannesburg",
            "country": "South Africa",
            "application_url": "https://apply.workable.com/j/407E4EFB53/apply",
        },
    ]
}


def test_scrape_merges_duplicate_city_rows_and_drops_non_pakistan_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.prime_system_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = PrimeSystemSolutionsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the South Africa-only job must be excluded

    first = jobs[0]
    assert first.title == "Trainee Engineer (Internship to Hire Program)"
    assert first.company == "Prime System Solutions"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://apply.workable.com/j/26B0160E9A/apply"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "System & Network Engineer (Level II)"
    assert second.location == "Islamabad, Lahore"  # both PK cities merged into one job, not duplicated


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.prime_system_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"jobs": []}, raise_for_status=lambda: None)

    jobs = PrimeSystemSolutionsScraper().scrape()

    assert jobs == []
