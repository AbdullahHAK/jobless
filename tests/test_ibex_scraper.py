from datetime import date

import requests

from jobless.scrapers.ibex import IbexScraper

SITEMAP_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://pktechcareers-ibex.icims.com/jobs/intro</loc></url>
    <url><loc>https://pktechcareers-ibex.icims.com/jobs/30180/technical-coordinator---pmo/job</loc></url>
    <url><loc>https://pktechcareers-ibex.icims.com/jobs/30177/analyst-software-qa-engineer/job</loc></url>
    <url><loc>https://pktechcareers-ibex.icims.com/jobs/99999/withdrawn-role/job</loc></url>
</urlset>
"""

JOB_PAGES = {
    "https://pktechcareers-ibex.icims.com/jobs/30180/technical-coordinator---pmo/job": (
        '<html><body><script type="application/ld+json">'
        '{"title": "Technical Coordinator - PMO", "jobLocation": '
        '[{"address": {"addressLocality": "Lahore"}}], '
        '"url": "https://pktechcareers-ibex.icims.com/jobs/30180/technical-coordinator---pmo/job"}'
        "</script></body></html>"
    ),
    "https://pktechcareers-ibex.icims.com/jobs/30177/analyst-software-qa-engineer/job": (
        '<html><body><script type="application/ld+json">'
        '{"title": "Analyst, Software QA Engineer", "jobLocation": '
        '[{"address": {"addressLocality": "Lahore"}}], '
        '"url": "https://pktechcareers-ibex.icims.com/jobs/30177/analyst-software-qa-engineer/job"}'
        "</script></body></html>"
    ),
}


def test_scrape_parses_json_ld_and_skips_withdrawn_postings(mocker):
    def fake_get(url, **kwargs):
        if url.endswith("sitemap.xml"):
            return mocker.Mock(content=SITEMAP_XML, raise_for_status=lambda: None)
        if url in JOB_PAGES:
            return mocker.Mock(text=JOB_PAGES[url], raise_for_status=lambda: None)

        def _raise_gone():
            raise requests.HTTPError("410 Gone")

        return mocker.Mock(raise_for_status=_raise_gone)

    mock_get = mocker.patch("jobless.scrapers.ibex.requests.get", side_effect=fake_get)

    jobs = IbexScraper().scrape()

    # 1 sitemap fetch + 3 job detail fetches (the intro welcome page is never fetched)
    assert mock_get.call_count == 4
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Technical Coordinator - PMO"
    assert first.company == "ibex"
    assert first.location == "Lahore"
    assert (
        str(first.apply_link)
        == "https://pktechcareers-ibex.icims.com/jobs/30180/technical-coordinator---pmo/job"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Analyst, Software QA Engineer"


def test_scrape_returns_empty_list_when_no_jobs_in_sitemap(mocker):
    empty_sitemap = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b"<url><loc>https://pktechcareers-ibex.icims.com/jobs/intro</loc></url>"
        b"</urlset>"
    )
    mock_get = mocker.patch(
        "jobless.scrapers.ibex.requests.get",
        return_value=mocker.Mock(content=empty_sitemap, raise_for_status=lambda: None),
    )

    jobs = IbexScraper().scrape()

    assert mock_get.call_count == 1  # only the sitemap - no detail pages fetched
    assert jobs == []
