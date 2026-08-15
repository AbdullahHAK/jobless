from datetime import date

from jobless.scrapers.genetech_solutions import GenetechSolutionsScraper

CAREERS_PAGE_HTML = """
<html><body>
<section class="jobs-listing">
  <div class="job-opened job-area-trigger" id="Other-Positions">
    <div class="share-icon"><div class="icon"></div><div class="testtt">
      <div id="mqIcon" class="job_social_share" data-id="other-positions"
        data-url="https://www.genetechsolutions.com/jobs#other-positions"></div>
    </div></div>
    <h3>Other Positions</h3>
    <h4 class="sub-text">Karachi, Pakistan</h4>
  </div>

  <div class="job-opened job-area-trigger" id="Content---Marketing-Specialist">
    <div class="share-icon"><div class="icon"></div><div class="testtt">
      <div id="mqIcon" class="job_social_share" data-id="content---marketing-specialist"
        data-url="https://www.genetechsolutions.com/jobs#content---marketing-specialist"></div>
    </div></div>
    <h3>Content &amp; Marketing Specialist</h3>
    <p class="sub-text">Minimum 1-2 of experience</p>
    <h4 class="sub-text">Karachi, Pakistan</h4>
  </div>

  <div class="job-opened job-area-trigger" id="Senior-SQA-Analyst-with-SmartBear-Experience">
    <div class="share-icon"><div class="icon"></div><div class="testtt">
      <div id="mqIcon" class="job_social_share" data-id="senior-sqa-analyst-with-smartbear-experience"
        data-url="https://www.genetechsolutions.com/jobs#senior-sqa-analyst-with-smartbear-experience"></div>
    </div></div>
    <h3>Senior SQA Analyst with SmartBear Experience</h3>
    <p class="sub-text">Minimum 5 Years of experience</p>
    <h4 class="sub-text">Karachi, Pakistan</h4>
  </div>
</section>
</body></html>
"""


def test_scrape_parses_job_cards_and_excludes_other_positions(mocker):
    mock_get = mocker.patch("jobless.scrapers.genetech_solutions.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = GenetechSolutionsScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the generic "Other Positions" catch-all must be excluded

    first = jobs[0]
    assert first.title == "Content & Marketing Specialist"
    assert first.company == "Genetech Solutions"
    assert first.location == "Karachi, Pakistan"
    assert str(first.apply_link) == "https://www.genetechsolutions.com/jobs#content---marketing-specialist"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior SQA Analyst with SmartBear Experience"
    assert str(second.apply_link) == "https://www.genetechsolutions.com/jobs#senior-sqa-analyst-with-smartbear-experience"


def test_scrape_returns_empty_list_when_no_cards_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.genetech_solutions.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = GenetechSolutionsScraper().scrape()

    assert jobs == []
