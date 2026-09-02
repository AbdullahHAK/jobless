from datetime import date

from jobless.scrapers.js_bank import JSBankScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="awsm-job-listing-item awsm-grid-item">
  <a href="https://www.jsbl.com/jobs/manager-infrastructure-and-engineering-projects-advisory/" class="awsm-job-item">
    <h2 class="awsm-job-post-title">Manager Infrastructure and Engineering Projects Advisory</h2>
    <div class="awsm-job-specification-job-location"><span class="awsm-job-specification-term">Karachi</span></div>
  </a>
</div>
<div class="awsm-job-listing-item awsm-job-expired-item awsm-grid-item">
  <a href="https://www.jsbl.com/?post_type=awsm_job_openings&p=463740" class="awsm-job-item">
    <h2 class="awsm-job-post-title">Title: Assistant Manager - Application Security</h2>
    <div class="awsm-job-specification-job-location"><span class="awsm-job-specification-term">Pakistan</span></div>
  </a>
</div>
<div class="awsm-job-listing-item awsm-grid-item">
  <a href="https://www.jsbl.com/jobs/senior-credit-analyst/" class="awsm-job-item">
    <h2 class="awsm-job-post-title">Senior Credit Analyst</h2>
    <div class="awsm-job-specification-job-location"><span class="awsm-job-specification-term">Karachi</span></div>
  </a>
</div>
</body></html>
"""


def test_scrape_excludes_expired_listings(mocker):
    mock_get = mocker.patch("jobless.scrapers.js_bank.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = JSBankScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the awsm-job-expired-item posting must be excluded

    first = jobs[0]
    assert first.title == "Manager Infrastructure and Engineering Projects Advisory"
    assert first.company == "JS Bank"
    assert first.location == "Karachi"
    assert (
        str(first.apply_link)
        == "https://www.jsbl.com/jobs/manager-infrastructure-and-engineering-projects-advisory/"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior Credit Analyst"


def test_scrape_returns_empty_list_when_no_listings_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.js_bank.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = JSBankScraper().scrape()

    assert jobs == []
