from datetime import date

from jobless.scrapers.euroshub import EurosHubScraper

# Shaped like the real page: Next.js streams the job list as a React Server
# Component payload inside a `self.__next_f.push([1, "<id>:<json>"])` inline
# script tag. The captured JSON string is itself `"<flight-id>:<json-array>"`,
# whose last element is `{"jobs": [...]}`.
JOBS_PAYLOAD = [
    "$",
    "$L21",
    None,
    {
        "jobs": [
            {
                "_id": "6a4ce6c5c624ac10af367814",
                "title": "Business Development Executive (On-Site)",
                "location": "Office 509, 5th Floor, Kohistan Tower, Saddar, Rawalpindi",
                "department": ["Business Development", "Sales", "Marketing"],
                "type": ["Full-time", "Fresher"],
            },
            {
                "_id": "6a0c0506c69d511e9511335e",
                "title": "Digital Marketing Specialist (On-site)",
                "location": "Office 509, 5th Floor, Kohistan Tower, Saddar, Rawalpindi",
                "department": ["Marketing", "Sales"],
                "type": ["Full-time", "Contract"],
            },
        ]
    },
]


def _build_html() -> str:
    import json

    inner_json = json.dumps(JOBS_PAYLOAD)
    flight_string = f"1b:{inner_json}\n"
    # This is what actually appears in the page source: a JS string literal
    # (JSON-escaped) passed to self.__next_f.push([1, "..."]).
    escaped = json.dumps(flight_string)
    return (
        "<html><body>"
        "<div>Careers page chrome the scraper should ignore</div>"
        f'<script>self.__next_f.push([1,{escaped}])</script>'
        "</body></html>"
    )


def test_scrape_parses_jobs_from_embedded_rsc_payload(mocker):
    mock_get = mocker.patch("jobless.scrapers.euroshub.requests.get")
    mock_get.return_value = mocker.Mock(text=_build_html(), raise_for_status=lambda: None)

    jobs = EurosHubScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Business Development Executive (On-Site)"
    assert first.company == "EurosHub"
    assert first.location == "Office 509, 5th Floor, Kohistan Tower, Saddar, Rawalpindi"
    assert str(first.apply_link) == "https://www.euroshub.com/career#openings"
    assert first.date_scraped == date.today()

    assert jobs[1].title == "Digital Marketing Specialist (On-site)"
    assert jobs[1].apply_link == first.apply_link


def test_scrape_returns_empty_list_when_no_rsc_jobs_chunk_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.euroshub.requests.get")
    mock_get.return_value = mocker.Mock(
        text="<html><body>No jobs chunk here</body></html>", raise_for_status=lambda: None
    )

    jobs = EurosHubScraper().scrape()

    assert jobs == []
