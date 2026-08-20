from datetime import date

from jobless.scrapers.smart_working_solutions import SmartWorkingSolutionsScraper

JOBS_PAYLOAD = [
    {
        "text": "AI Agent Engineer (Remote, Full-Time) [AS311] (PK)",
        "hostedUrl": "https://jobs.lever.co/smart-working-solutions/1f7a713e-d86c-48b8-9252-6554246611bf",
        "categories": {"location": "Pakistan", "allLocations": ["Pakistan"]},
    },
    {
        "text": "Lead PHP/Symfony Engineer (Remote, Full-Time) - [HR191] (PK)",
        "hostedUrl": "https://jobs.lever.co/smart-working-solutions/2c914f64-f1f7-47c7-b81c-b1357965d7bd",
        "categories": {
            "location": "Lahore",
            "allLocations": ["Lahore", "Abbottabad", "Hyderabad, Pakistan"],
        },
    },
    {
        "text": "Full-Stack Web Engineer (Remote, Full-Time)",
        "hostedUrl": "https://jobs.lever.co/smart-working-solutions/9e0e57ef-64ad-4e09-a307-d20640fdd660",
        "categories": {"location": "India", "allLocations": ["India", "Delhi"]},
    },
]


def test_scrape_keeps_only_pakistan_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.smart_working_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = SmartWorkingSolutionsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the India-only posting must be excluded

    first = jobs[0]
    assert first.title == "AI Agent Engineer (Remote, Full-Time) [AS311] (PK)"
    assert first.company == "Smart Working Solutions"
    assert first.location == "Pakistan"
    assert (
        str(first.apply_link)
        == "https://jobs.lever.co/smart-working-solutions/1f7a713e-d86c-48b8-9252-6554246611bf"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Lead PHP/Symfony Engineer (Remote, Full-Time) - [HR191] (PK)"
    assert second.location == "Lahore"  # primary location kept even though "Pakistan" only matched via allLocations


def test_scrape_returns_empty_list_when_no_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.smart_working_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: [], raise_for_status=lambda: None)

    jobs = SmartWorkingSolutionsScraper().scrape()

    assert jobs == []
