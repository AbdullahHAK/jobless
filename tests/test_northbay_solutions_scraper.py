from datetime import date

from jobless.scrapers.northbay_solutions import NorthBaySolutionsScraper

JOBS_PAYLOAD = [
    {
        "title": "Vmware Administrator",
        "country_id": "Pakistan",
        "city": "Lahore",
        "board_code": "TFrp8nPfMY",
    },
    {
        "title": "Solution Architect - Microsoft Dynamics 365",
        "country_id": "Pakistan",
        "city": "",
        "board_code": "qSEQ952ROQ",
    },
    {
        "title": "Linux Administrator",
        "country_id": "United Arab Emirates",
        "city": "Dubai",
        "board_code": "ZZZ999999",
    },
]


def test_scrape_keeps_only_pakistan_country_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.northbay_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = NorthBaySolutionsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the UAE-tagged role is excluded

    first = jobs[0]
    assert first.title == "Vmware Administrator"
    assert first.company == "NorthBay Solutions"
    assert first.location == "Lahore, Pakistan"
    assert str(first.apply_link) == "https://northbay.applytojob.com/apply/TFrp8nPfMY"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Solution Architect - Microsoft Dynamics 365"
    assert second.location == "Pakistan"  # no city given for this posting


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_get = mocker.patch("jobless.scrapers.northbay_solutions.requests.get")
    mock_get.return_value = mocker.Mock(json=lambda: [], raise_for_status=lambda: None)

    jobs = NorthBaySolutionsScraper().scrape()

    assert jobs == []
