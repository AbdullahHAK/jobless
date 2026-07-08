from datetime import date

from jobless.scrapers.abacus_consulting import AbacusConsultingScraper

PAGE_ONE_HTML = """
<html>
<body>
  <div class="page-indicator"><span class="heading-font">Page 1 of 2</span></div>
  <article class="mb-3 job-card">
    <a class="job-title-link" data-job-id="11111111-1111-1111-1111-111111111111"
       data-job-title="Apigee Architect" data-job-city="" data-job-country=""
       href="/jobs/11111111-1111-1111-1111-111111111111">
      <h6 class="job-title mb-0">Apigee Architect</h6>
    </a>
  </article>
  <article class="mb-3 job-card">
    <a class="job-title-link" data-job-id="22222222-2222-2222-2222-222222222222"
       data-job-title="Accounts Executive" data-job-city="Lahore" data-job-country="Pakistan"
       href="/jobs/22222222-2222-2222-2222-222222222222">
      <h6 class="job-title mb-0">Accounts Executive</h6>
    </a>
  </article>
</body>
</html>
"""

PAGE_TWO_HTML = """
<html>
<body>
  <div class="page-indicator"><span class="heading-font">Page 2 of 2</span></div>
  <article class="mb-3 job-card">
    <a class="job-title-link" data-job-id="33333333-3333-3333-3333-333333333333"
       data-job-title="Procurement Executive" data-job-city="Lahore" data-job-country="Pakistan"
       href="/jobs/33333333-3333-3333-3333-333333333333">
      <h6 class="job-title mb-0">Procurement Executive</h6>
    </a>
  </article>
</body>
</html>
"""

SINGLE_PAGE_HTML = """
<html>
<body>
  <div class="page-indicator"><span class="heading-font">Page 1 of 1</span></div>
  <article class="mb-3 job-card">
    <a class="job-title-link" data-job-id="11111111-1111-1111-1111-111111111111"
       data-job-title="Apigee Architect" data-job-city="" data-job-country=""
       href="/jobs/11111111-1111-1111-1111-111111111111">
      <h6 class="job-title mb-0">Apigee Architect</h6>
    </a>
  </article>
</body>
</html>
"""


def test_scrape_follows_pagination_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.abacus_consulting.requests.get")
    mock_get.side_effect = [
        mocker.Mock(text=PAGE_ONE_HTML, status_code=200, raise_for_status=lambda: None),
        mocker.Mock(text=PAGE_TWO_HTML, status_code=200, raise_for_status=lambda: None),
    ]
    mocker.patch("jobless.scrapers.abacus_consulting.time.sleep")

    jobs = AbacusConsultingScraper().scrape()

    assert mock_get.call_count == 2
    assert len(jobs) == 3

    first = jobs[0]
    assert first.title == "Apigee Architect"
    assert first.company == "Abacus Consulting"
    assert first.location == "Not specified"
    assert (
        str(first.apply_link)
        == "https://abacus-consulting-3.careers-page.com/jobs/11111111-1111-1111-1111-111111111111"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Accounts Executive"
    assert second.location == "Lahore, Pakistan"

    third = jobs[2]
    assert third.title == "Procurement Executive"
    assert third.location == "Lahore, Pakistan"


def test_scrape_backs_off_and_retries_on_rate_limit(mocker):
    mock_get = mocker.patch("jobless.scrapers.abacus_consulting.requests.get")
    rate_limited = mocker.Mock(status_code=429)
    rate_limited.raise_for_status.side_effect = AssertionError(
        "raise_for_status should not be called for a 429 response"
    )
    mock_get.side_effect = [
        rate_limited,
        mocker.Mock(text=SINGLE_PAGE_HTML, status_code=200, raise_for_status=lambda: None),
    ]
    mock_sleep = mocker.patch("jobless.scrapers.abacus_consulting.time.sleep")

    jobs = AbacusConsultingScraper().scrape()

    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()
    assert len(jobs) == 1
    assert jobs[0].title == "Apigee Architect"
