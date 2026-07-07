from datetime import date

from jobless.scrapers.contour_software import ContourSoftwareScraper

PAGE_ONE = {
    "total": 2,
    "jobPostings": [
        {
            "title": "Sr. SQA Automation Analyst",
            "externalPath": "/job/PER---Karachi-PK/Sr-SQA-Automation-Analyst_R52907",
            "timeType": "Full time",
            "locationsText": "PER - Karachi, PK",
            "postedOn": "Posted Today",
            "bulletFields": ["R52907"],
        }
    ],
    "facets": [],
    "userAuthenticated": False,
}

PAGE_TWO = {
    "total": 2,
    "jobPostings": [
        {
            "title": "Software Architect",
            "externalPath": "/job/PER---Lahore-PK/Software-Architect_R51577",
            "timeType": "Full time",
            "locationsText": "3 Locations",
            "postedOn": "Posted 7 Days Ago",
            "bulletFields": ["R51577"],
        }
    ],
    "facets": [],
    "userAuthenticated": False,
}


def test_scrape_follows_pagination_and_builds_job_schema(mocker):
    mock_post = mocker.patch("jobless.scrapers.contour_software.requests.post")
    mock_post.side_effect = [
        mocker.Mock(json=lambda: PAGE_ONE, raise_for_status=lambda: None),
        mocker.Mock(json=lambda: PAGE_TWO, raise_for_status=lambda: None),
    ]
    mocker.patch("jobless.scrapers.contour_software.time.sleep")

    jobs = ContourSoftwareScraper().scrape()

    assert mock_post.call_count == 2
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Sr. SQA Automation Analyst"
    assert first.company == "Contour Software"
    assert first.location == "PER - Karachi, PK"
    assert (
        str(first.apply_link)
        == "https://contour-software.com/job-detail/?jobPath=%2Fjob%2FPER---Karachi-PK%2FSr-SQA-Automation-Analyst_R52907&jobTitle=Sr.%20SQA%20Automation%20Analyst"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Software Architect"
    assert second.location == "3 Locations"

    # First call requests offset=0, second call requests offset=1 (after 1 result).
    first_call_kwargs = mock_post.call_args_list[0].kwargs
    second_call_kwargs = mock_post.call_args_list[1].kwargs
    assert first_call_kwargs["json"]["offset"] == 0
    assert second_call_kwargs["json"]["offset"] == 1
