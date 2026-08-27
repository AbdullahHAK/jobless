from datetime import date

from jobless.scrapers.bazaar_technologies import BazaarTechnologiesScraper

JOBS_PAYLOAD = {
    "count": 3,
    "results": [
        {
            "position_name": "B2C Operations Manager",
            "location_display": "Karachi, Pakistan",
            "hash": "L9YY5534",
        },
        {
            "position_name": "Bazaar Talent Pool - Engineering",
            "location_display": "",
            "hash": "L987YR44",
        },
        {
            "position_name": "Head of Last Mile",
            "location_display": "Karachi, Pakistan",
            "hash": "L556V5R5",
        },
    ],
}


def test_scrape_excludes_talent_pool_entries(mocker):
    mock_get = mocker.patch("jobless.scrapers.bazaar_technologies.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = BazaarTechnologiesScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the "Bazaar Talent Pool" catch-all must be excluded

    first = jobs[0]
    assert first.title == "B2C Operations Manager"
    assert first.company == "Bazaar Technologies"
    assert first.location == "Karachi, Pakistan"
    assert str(first.apply_link) == "https://www.careers-page.com/bazaar-technologies/job/L9YY5534"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Head of Last Mile"
    assert str(second.apply_link) == "https://www.careers-page.com/bazaar-technologies/job/L556V5R5"


def test_scrape_returns_empty_list_when_no_results(mocker):
    mock_get = mocker.patch("jobless.scrapers.bazaar_technologies.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: {"count": 0, "results": []}, raise_for_status=lambda: None)

    jobs = BazaarTechnologiesScraper().scrape()

    assert jobs == []
