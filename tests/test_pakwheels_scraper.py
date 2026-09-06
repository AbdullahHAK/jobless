from datetime import date

from jobless.scrapers.pakwheels import PakWheelsScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="featured-jobs">
  <a class="list-group-item" href="//pakeventures.simplicant.com/jobs/61410-senior-software-engineer/detail">
    <h3 class="job-title">Senior Software Engineer</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
</div>
<div class="list-group list-jobs">
  <a class="list-group-item" href="//pakeventures.simplicant.com/jobs/61410-senior-software-engineer/detail">
    <h3 class="job-title">Senior Software Engineer</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
  <a class="list-group-item" href="//pakeventures.simplicant.com/jobs/62252-finance-intern/detail">
    <h3 class="job-title">Finance Intern</h3>
    <div class="job-subtitle">Lahore, Punjab, Pakistan</div>
  </a>
</div>
</body></html>
"""


def test_scrape_dedupes_by_href(mocker):
    mock_get = mocker.patch("jobless.scrapers.pakwheels.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = PakWheelsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the featured-section copy of Senior Software Engineer must not duplicate

    first = jobs[0]
    assert first.title == "Senior Software Engineer"
    assert first.company == "PakWheels"
    assert first.location == "Lahore, Punjab, Pakistan"
    assert (
        str(first.apply_link) == "https://pakeventures.simplicant.com/jobs/61410-senior-software-engineer/detail"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Finance Intern"


def test_scrape_returns_empty_list_when_no_job_links_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.pakwheels.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = PakWheelsScraper().scrape()

    assert jobs == []
