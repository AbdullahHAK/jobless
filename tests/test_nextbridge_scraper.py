from datetime import date

from jobless.scrapers.nextbridge import NextbridgeScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="job-list-wrapper">
  <div class="job-list" id="job-list">
    <table>
      <tr>
        <th>Job Title</th>
        <th>Location</th>
        <th>Apply Now</th>
      </tr>
      <tr>
        <td class="talent-acquisition-job-title">
          <a href="https://nextbridge.com/job-detail?job_id=6a4514ddcd7c8c73086dc031">Electrical Engineer Trainee</a>
        </td>
        <td>Lahore,Pakistan</td>
        <td><a href="https://nextbridge.com/job-detail?job_id=6a4514ddcd7c8c73086dc031">Apply Now</a></td>
      </tr>
      <tr>
        <td class="talent-acquisition-job-title">
          <a href="https://nextbridge.com/job-detail?job_id=6a27e362f058597d06bb9677">Power BI Developer</a>
        </td>
        <td>Lahore,Pakistan</td>
        <td><a href="https://nextbridge.com/job-detail?job_id=6a27e362f058597d06bb9677">Apply Now</a></td>
      </tr>
    </table>
  </div>
</div>
</body></html>
"""


def test_scrape_parses_job_rows_from_static_html(mocker):
    mock_get = mocker.patch("jobless.scrapers.nextbridge.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = NextbridgeScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Electrical Engineer Trainee"
    assert first.company == "Nextbridge"
    assert first.location == "Lahore,Pakistan"
    assert str(first.apply_link) == "https://nextbridge.com/job-detail?job_id=6a4514ddcd7c8c73086dc031"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Power BI Developer"
    assert str(second.apply_link) == "https://nextbridge.com/job-detail?job_id=6a27e362f058597d06bb9677"


def test_scrape_returns_empty_list_when_job_list_missing(mocker):
    mock_get = mocker.patch("jobless.scrapers.nextbridge.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = NextbridgeScraper().scrape()

    assert jobs == []
