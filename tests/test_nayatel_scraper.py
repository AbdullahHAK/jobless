from datetime import date

from jobless.scrapers.nayatel import NayatelScraper

JOBS_PAYLOAD = {
    "message": "Data Found Successfully",
    "data": [
        {
            "ID": 80131,
            "JOBTITLE": "Deputy Manager( Corporate & Legal Affairs )",
            "JOBLOCATION": "Gujranwala",
        },
        {
            "ID": 83131,
            "JOBTITLE": "Full Stack Developer( Creative Solutions )",
            "JOBLOCATION": "Islamabad",
        },
    ],
}


def test_scrape_parses_all_jobs_from_the_api(mocker):
    mock_post = mocker.patch("jobless.scrapers.nayatel.requests.post")
    mock_post.return_value = mocker.Mock(json=lambda: JOBS_PAYLOAD, raise_for_status=lambda: None)

    jobs = NayatelScraper().scrape()

    assert mock_post.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Deputy Manager( Corporate & Legal Affairs )"
    assert first.company == "Nayatel"
    assert first.location == "Gujranwala, Pakistan"
    assert str(first.apply_link) == "https://careers.nayatel.com/vacant-positions/80131"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Full Stack Developer( Creative Solutions )"
    assert second.location == "Islamabad, Pakistan"
    assert str(second.apply_link) == "https://careers.nayatel.com/vacant-positions/83131"


def test_scrape_returns_empty_list_when_no_jobs(mocker):
    mock_post = mocker.patch("jobless.scrapers.nayatel.requests.post")
    mock_post.return_value = mocker.Mock(json=lambda: {"message": "No active jobs found", "data": []}, raise_for_status=lambda: None)

    jobs = NayatelScraper().scrape()

    assert jobs == []
