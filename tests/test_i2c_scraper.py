import json
from datetime import date

from jobless.scrapers.i2c import I2cScraper

CAREERS_PAGE_HTML = """
<html><body>
<form action="#" class="filter-jobs-form">
<input type="hidden" name="csrf_token" value="abc123token" />
</form>
</body></html>
"""

AJAX_RESPONSE_HTML = """
<div class="job-tile"><article class="joblisting-box">
  <a href="index.php/showjob/principal-data-scientist" aria-label="Principal Data Scientist">
    <div class="joblisting-left"><h2 class="text-xl">Principal Data Scientist</h2></div>
    <div class="joblisting-right">
      <span class="joblisting-dept text-sm">Engineering</span>
      <span class="joblisting-location text-sm">Pakistan</span>
    </div>
  </a>
</article></div>
<div class="job-tile"><article class="joblisting-box">
  <a href="index.php/showjob/risk-analyst" aria-label="Risk Analyst">
    <div class="joblisting-left"><h2 class="text-xl">Risk Analyst</h2></div>
    <div class="joblisting-right">
      <span class="joblisting-dept text-sm">Risk</span>
      <span class="joblisting-location text-sm">Pakistan</span>
    </div>
  </a>
</article></div>
"""


def _mock_session(mocker, ajax_json):
    session = mocker.Mock()
    session.get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)
    session.post.return_value = mocker.Mock(json=lambda: ajax_json, raise_for_status=lambda: None)
    mocker.patch("jobless.scrapers.i2c.requests.Session", return_value=session)
    return session


def test_scrape_parses_job_tiles_from_ajax_response(mocker):
    ajax_json = {"html": AJAX_RESPONSE_HTML, "totalOpenings": 29, "jobCount": 16}
    session = _mock_session(mocker, ajax_json)

    jobs = I2cScraper().scrape()

    assert session.get.call_count == 1
    assert session.post.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Principal Data Scientist"
    assert first.company == "i2c Inc"
    assert first.location == "Pakistan"
    assert str(first.apply_link) == "https://careers.i2cinc.com/careers/index.php/showjob/principal-data-scientist"
    assert first.date_scraped == date.today()

    # The CSRF token scraped from the GET response must actually be the one
    # sent on the POST - not hardcoded or forgotten.
    _, post_kwargs = session.post.call_args
    sent_filters = post_kwargs["data"]
    assert sent_filters["csrf_token"] == "abc123token"
    assert json.loads(sent_filters["filters"]) == {"location": ["Pakistan"]}


def test_scrape_returns_empty_list_when_csrf_token_missing(mocker):
    session = mocker.Mock()
    session.get.return_value = mocker.Mock(text="<html><body>no form here</body></html>", raise_for_status=lambda: None)
    mocker.patch("jobless.scrapers.i2c.requests.Session", return_value=session)

    jobs = I2cScraper().scrape()

    assert jobs == []
    session.post.assert_not_called()


def test_scrape_returns_empty_list_when_no_tiles_present(mocker):
    ajax_json = {"html": "<p>No openings</p>"}
    _mock_session(mocker, ajax_json)

    jobs = I2cScraper().scrape()

    assert jobs == []
