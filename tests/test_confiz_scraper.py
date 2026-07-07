from datetime import date

from jobless.scrapers.confiz import ConfizScraper

# Shaped like the real https://confiz.simplicant.com/ response: a "Featured
# Jobs" section (protocol-relative links) that duplicates a subset of the
# postings shown again further down, grouped under per-location <h2> headings.
JOB_BOARD_HTML = """
<html>
<body>
<div class="jobs-listings" id="jobs_listings">
  <h2 class="heading heading-featured">Our Featured Jobs</h2>
  <div class="panel panel-jobboard">
    <div class="list-group list-jobs">
      <a class="list-group-item" id="61685_job_link" data-job-detail-id="61685_feature_job_detail" href="//confiz.simplicant.com/jobs/61685-ai-security-engineer/detail">
        <h3 class="list-group-item-title job-title">AI Security Engineer</h3>
        <div class="list-group-item-subtitle job-subtitle">Lahore, Islamabad, Karachi, Pakistan</div>
      </a>
    </div>
    <h2 class="heading">Lahore, Punjab, Pakistan</h2>
    <div class="list-group list-jobs">
      <a class="list-group-item" id="61228_job_link" data-job-detail-id="61228_job_detail" href="//confiz.simplicant.com/jobs/61228-scrum-master/detail">
        <h3 class="list-group-item-title job-title">Scrum Master</h3>
        <div class="list-group-item-subtitle job-subtitle">Delivery</div>
      </a>
    </div>
    <h2 class="heading">Lahore, Islamabad, Karachi, Pakistan</h2>
    <div class="list-group list-jobs">
      <a class="list-group-item" id="61685_job_link" data-job-detail-id="61685_job_detail" href="//confiz.simplicant.com/jobs/61685-ai-security-engineer/detail">
        <h3 class="list-group-item-title job-title">AI Security Engineer</h3>
        <div class="list-group-item-subtitle job-subtitle">Information Technology</div>
      </a>
      <a class="list-group-item" id="61211_job_link" data-job-detail-id="61211_job_detail" href="//confiz.simplicant.com/jobs/61211-ai-solution-architect/detail">
        <h3 class="list-group-item-title job-title">AI Solution Architect</h3>
        <div class="list-group-item-subtitle job-subtitle">Delivery</div>
      </a>
    </div>
  </div>
</div>
</body>
</html>
"""


def test_scrape_parses_location_groups_and_dedupes_featured_section(mocker):
    mock_get = mocker.patch("jobless.scrapers.confiz.requests.get")
    mock_get.return_value = mocker.Mock(text=JOB_BOARD_HTML, raise_for_status=lambda: None)

    jobs = ConfizScraper().scrape()

    assert mock_get.call_count == 1
    # 3 unique postings total, even though "AI Security Engineer" appears
    # once in the featured section and once in its location group.
    assert len(jobs) == 3

    first = jobs[0]
    assert first.title == "Scrum Master"
    assert first.company == "Confiz"
    assert first.location == "Lahore, Punjab, Pakistan"
    assert str(first.apply_link) == "https://confiz.simplicant.com/jobs/61228-scrum-master/detail"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "AI Security Engineer"
    assert second.location == "Lahore, Islamabad, Karachi, Pakistan"
    assert str(second.apply_link) == "https://confiz.simplicant.com/jobs/61685-ai-security-engineer/detail"

    third = jobs[2]
    assert third.title == "AI Solution Architect"
    assert third.location == "Lahore, Islamabad, Karachi, Pakistan"
    assert str(third.apply_link) == "https://confiz.simplicant.com/jobs/61211-ai-solution-architect/detail"
