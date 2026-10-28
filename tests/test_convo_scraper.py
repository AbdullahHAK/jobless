from datetime import date

from jobless.scrapers.convo import ConvoScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="js-job-departament-container">
  <div class="js-job-department">Backend Dev</div>
  <div class="js-job-container">
    <div class="js-row js-job-list-item" data-url="/careers/convo/jobs/senior-ai-engineer-abc">
      <div class="js-job-title-wrapper">
        <span class="js-job-title">
          <a href="/careers/convo/jobs/senior-ai-engineer-abc">Senior AI Engineer - Agentic AI &amp; Python</a>
        </span>
      </div>
      <div class="js-job-location-wrapper">
        <span class="js-job-location">Hybrid in Islamabad, Punjab Province and Federal Capital Territory (ICT), Pakistan</span>
      </div>
    </div>
    <div class="js-row js-job-list-item" data-url="/careers/convo/jobs/senior-devops-engineer-def">
      <div class="js-job-title-wrapper">
        <span class="js-job-title">
          <a href="/careers/convo/jobs/senior-devops-engineer-def">Senior DevOps Engineer - Agentic Platform</a>
        </span>
      </div>
      <div class="js-job-location-wrapper">
        <span class="js-job-location">Islamabad, Islamabad Capital Territory, Pakistan</span>
      </div>
    </div>
  </div>
</div>
<div class="js-job-departament-container">
  <div class="js-job-department">Sales</div>
  <div class="js-job-container">
    <div class="js-row js-job-list-item" data-url="/careers/convo/jobs/account-executive-ghi">
      <div class="js-job-title-wrapper">
        <span class="js-job-title">
          <a href="/careers/convo/jobs/account-executive-ghi">Account Executive</a>
        </span>
      </div>
      <div class="js-job-location-wrapper">
        <span class="js-job-location">San Francisco, CA</span>
      </div>
    </div>
  </div>
</div>
</body></html>
"""


def test_scrape_keeps_only_pakistan_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.convo.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = ConvoScraper().scrape()

    assert mock_get.call_count == 1
    # The San Francisco role is excluded.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior AI Engineer - Agentic AI & Python"
    assert first.company == "Convo"
    assert "Islamabad" in first.location
    assert str(first.apply_link) == "https://careers.jobscore.com/careers/convo/jobs/senior-ai-engineer-abc"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior DevOps Engineer - Agentic Platform"


def test_scrape_returns_empty_list_when_no_postings_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.convo.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = ConvoScraper().scrape()

    assert jobs == []
