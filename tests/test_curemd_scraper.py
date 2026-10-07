from datetime import date

from jobless.scrapers.curemd import CureMDScraper

PAGE_ONE = {
    "total": 2,
    "jobPostings": [
        {
            "title": "Software Engineer",
            "externalPath": "/job/Lahore/Software-Engineer_JR102204",
            "locationsText": "Lahore",
            "postedOn": "Posted 30+ Days Ago",
        },
        {
            "title": "Intern - HR Business Partner",
            "externalPath": "/job/Remote---PAK/Intern---HR-Business-Partner_JR102300",
            "locationsText": "Remote - PAK",
            "postedOn": "Posted 10 Days Ago",
        },
    ],
}
PAGE_TWO = {
    "total": 0,
    "jobPostings": [
        {
            "title": "SOC Analyst L1",
            "externalPath": "/job/Lahore/SOC-Analyst-L1_JR102296",
            "locationsText": "Lahore",
            "postedOn": "Posted 6 Days Ago",
        },
    ],
}
EMPTY_PAGE = {"total": 0, "jobPostings": []}


def test_scrape_paginates_until_a_short_page_is_returned(mocker):
    mocker.patch("jobless.scrapers.curemd.PAGE_SIZE", 2)
    mock_post = mocker.patch("jobless.scrapers.curemd.requests.post")
    mock_post.side_effect = [
        mocker.Mock(json=lambda: PAGE_ONE, raise_for_status=lambda: None),
        mocker.Mock(json=lambda: PAGE_TWO, raise_for_status=lambda: None),
    ]

    jobs = CureMDScraper().scrape()

    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0].kwargs["json"]["offset"] == 0
    assert mock_post.call_args_list[1].kwargs["json"]["offset"] == 2
    assert len(jobs) == 3

    first = jobs[0]
    assert first.title == "Software Engineer"
    assert first.company == "CureMD"
    assert first.location == "Lahore"
    assert (
        str(first.apply_link) == "https://curemd.wd1.myworkdayjobs.com/CureMD/job/Lahore/Software-Engineer_JR102204"
    )
    assert first.date_scraped == date.today()

    intern = jobs[1]
    assert intern.title == "Intern - HR Business Partner"
    assert intern.location == "Remote - PAK"


def test_scrape_stops_after_a_single_short_page(mocker):
    mocker.patch("jobless.scrapers.curemd.PAGE_SIZE", 20)
    mock_post = mocker.patch("jobless.scrapers.curemd.requests.post")
    mock_post.return_value = mocker.Mock(json=lambda: EMPTY_PAGE, raise_for_status=lambda: None)

    jobs = CureMDScraper().scrape()

    assert mock_post.call_count == 1
    assert jobs == []


def test_scrape_stops_when_a_page_repeats_already_seen_postings(mocker):
    # Real incident (2026-10-07): once `offset` passed the true end of
    # results, Workday kept re-returning a full, repeated PAGE_SIZE page
    # forever instead of ever returning a short one - the old
    # len(postings) < PAGE_SIZE check could never fire, and the scraper
    # looped until a live CI run hit its 15-minute job timeout. A page
    # that contributes nothing new must stop pagination immediately,
    # regardless of its length.
    mocker.patch("jobless.scrapers.curemd.PAGE_SIZE", 1)
    mock_post = mocker.patch("jobless.scrapers.curemd.requests.post")
    repeated_page = {
        "total": 1,
        "jobPostings": [
            {
                "title": "Software Engineer",
                "externalPath": "/job/Lahore/Software-Engineer_JR102204",
                "locationsText": "Lahore",
                "postedOn": "Posted 30+ Days Ago",
            },
        ],
    }
    # Every page - including ones past the real end of data - returns the
    # exact same single posting, full-length (never short), simulating the
    # real wraparound behavior.
    mock_post.return_value = mocker.Mock(json=lambda: repeated_page, raise_for_status=lambda: None)

    jobs = CureMDScraper().scrape()

    assert len(jobs) == 1
    # Must stop on the second request (first repeat), not run away.
    assert mock_post.call_count == 2


def test_scrape_stops_at_the_max_pages_safety_cap_and_warns(mocker, caplog):
    mocker.patch("jobless.scrapers.curemd.PAGE_SIZE", 1)
    mocker.patch("jobless.scrapers.curemd.MAX_PAGES", 3)
    mock_post = mocker.patch("jobless.scrapers.curemd.requests.post")
    # A distinct, never-repeating posting on every page, so dedup alone
    # never stops it - only the MAX_PAGES cap can.
    mock_post.side_effect = [
        mocker.Mock(
            json=lambda i=i: {
                "total": 999,
                "jobPostings": [
                    {
                        "title": f"Role {i}",
                        "externalPath": f"/job/Lahore/Role-{i}",
                        "locationsText": "Lahore",
                        "postedOn": "Posted recently",
                    }
                ],
            },
            raise_for_status=lambda: None,
        )
        for i in range(10)
    ]

    jobs = CureMDScraper().scrape()

    assert mock_post.call_count == 3
    assert len(jobs) == 3
    assert "safety cap" in caplog.text
