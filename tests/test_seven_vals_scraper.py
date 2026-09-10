from datetime import date

from jobless.scrapers.seven_vals import SevenValsScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="featured-jobs">
  <a class="list-group-item" href="//7vals.simplicant.com/jobs/1-devops-engineer/detail">
    <h3 class="job-title">DevOps Engineer</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
</div>
<div class="list-group list-jobs">
  <a class="list-group-item" href="//7vals.simplicant.com/jobs/1-devops-engineer/detail">
    <h3 class="job-title">DevOps Engineer</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
  <a class="list-group-item" href="//7vals.simplicant.com/jobs/2-software-qa-engineer/detail">
    <h3 class="job-title">Software Quality Assurance Engineer</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
</div>
</body></html>
"""


def test_scrape_dedupes_by_href(mocker):
    mock_get = mocker.patch("jobless.scrapers.seven_vals.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = SevenValsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the featured-section copy of DevOps Engineer must not duplicate

    first = jobs[0]
    assert first.title == "DevOps Engineer"
    assert first.company == "7Vals"
    assert first.location == "Lahore, Punjab, Pakistan"
    assert str(first.apply_link) == "https://7vals.simplicant.com/jobs/1-devops-engineer/detail"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Software Quality Assurance Engineer"


def test_scrape_returns_empty_list_when_no_job_links_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.seven_vals.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = SevenValsScraper().scrape()

    assert jobs == []
