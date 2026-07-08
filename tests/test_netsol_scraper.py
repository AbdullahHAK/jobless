from datetime import date

from jobless.scrapers.netsol import NetSolScraper

PAGE_ONE_HTML = """
<html><body>
<div class="noo-main" role="main">
    <article class="loadmore-item noo_job style-1 post-101 type-noo_job status-publish hentry
                     job_category-software-web-development job_location-lahore no-featured"
             data-url="https://careers.netsoltech.com/openings/software-engineer-net-2/">
        <a class="job-details-link" href="https://careers.netsoltech.com/openings/software-engineer-net-2/"></a>
        <div class="loop-item-wrap list">
            <div class="loop-item-content">
                <h3 class="loop-item-title">
                    <a href="https://careers.netsoltech.com/openings/software-engineer-net-2/"
                       title="Permanent link to: &quot;Software Engineer (.NET)&quot;">Software Engineer (.NET)</a>
                </h3>
                <p class="content-meta">
                    <span class="job-location">
                        <a href="https://careers.netsoltech.com/job-location/lahore/"><em>Lahore</em></a>
                    </span>
                    <span class="job-date">
                        <time class="entry-date" datetime="2026-06-01T00:00:00+00:00">June 1, 2026</time>
                    </span>
                    <span class="job-category">
                        <a href="https://careers.netsoltech.com/job-category/software-web-development/"
                           title="View all posts in">Software &amp; Web Development</a>
                    </span>
                </p>
            </div>
        </div>
    </article>
    <div class="pagination list-center">
        <span aria-current="page" class="page-numbers current">1</span>
        <a class="page-numbers" href="https://careers.netsoltech.com/openings/page/2/">2</a>
        <a class="next page-numbers" href="https://careers.netsoltech.com/openings/page/2/">Next</a>
    </div>
</div>
</body></html>
"""

PAGE_TWO_HTML = """
<html><body>
<div class="noo-main" role="main">
    <article class="loadmore-item noo_job style-1 post-102 type-noo_job status-publish hentry
                     job_category-quality-assurance job_location-islamabad no-featured"
             data-url="https://careers.netsoltech.com/openings/qa-engineer/">
        <a class="job-details-link" href="https://careers.netsoltech.com/openings/qa-engineer/"></a>
        <div class="loop-item-wrap list">
            <div class="loop-item-content">
                <h3 class="loop-item-title">
                    <a href="https://careers.netsoltech.com/openings/qa-engineer/"
                       title="Permanent link to: &quot;QA Engineer&quot;">QA Engineer</a>
                </h3>
                <p class="content-meta">
                    <span class="job-location">
                        <a href="https://careers.netsoltech.com/job-location/islamabad/"><em>Islamabad</em></a>
                    </span>
                    <span class="job-category">
                        <a href="https://careers.netsoltech.com/job-category/quality-assurance/"
                           title="View all posts in">Quality Assurance</a>
                    </span>
                </p>
            </div>
        </div>
    </article>
    <div class="pagination list-center">
        <span aria-current="page" class="page-numbers current">2</span>
    </div>
</div>
</body></html>
"""

NO_JOBS_HTML = """
<html><body>
<div class="noo-main" role="main">
    <h3 class="text-center">Sorry, No job available for now.</h3>
</div>
</body></html>
"""


def test_scrape_follows_pagination_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.netsol.requests.get")
    mock_get.side_effect = [
        mocker.Mock(text=PAGE_ONE_HTML, raise_for_status=lambda: None),
        mocker.Mock(text=PAGE_TWO_HTML, raise_for_status=lambda: None),
    ]
    mocker.patch("jobless.scrapers.netsol.time.sleep")

    jobs = NetSolScraper().scrape()

    assert mock_get.call_count == 2
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Software Engineer (.NET)"
    assert first.company == "NetSol Technologies"
    assert first.location == "Lahore"
    assert str(first.apply_link) == "https://careers.netsoltech.com/openings/software-engineer-net-2/"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "QA Engineer"
    assert second.location == "Islamabad"
    assert str(second.apply_link) == "https://careers.netsoltech.com/openings/qa-engineer/"


def test_scrape_returns_empty_list_when_no_jobs_available(mocker):
    mock_get = mocker.patch("jobless.scrapers.netsol.requests.get")
    mock_get.return_value = mocker.Mock(text=NO_JOBS_HTML, raise_for_status=lambda: None)
    mocker.patch("jobless.scrapers.netsol.time.sleep")

    jobs = NetSolScraper().scrape()

    assert mock_get.call_count == 1
    assert jobs == []
