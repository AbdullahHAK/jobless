from datetime import date

from jobless.scrapers.nayapay import NayaPayScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="job-postion-card-holder">
  <div class="simple-info-holder">
    <div class="simple-info">
      <h5 class="semi-bold">Creative Designer</h5>
      <h5 class="position-location">Karachi</h5>
    </div>
  </div>
  <div class="more-info-holder">
    <a class="main-button-2 apply" href="mailto:careers@nayapay.com?subject=Creative Designer">Apply</a>
  </div>
</div>
<div class="job-postion-card-holder">
  <div class="simple-info-holder">
    <div class="simple-info">
      <h5 class="semi-bold">DevOps Engineer</h5>
      <h5 class="position-location"></h5>
    </div>
  </div>
  <div class="more-info-holder">
    <a class="main-button-2 apply" href="mailto:careers@nayapay.com?subject=DevOps Engineer">Apply</a>
  </div>
</div>
</body></html>
"""


def test_scrape_parses_job_cards_and_builds_anchor_apply_links(mocker):
    mock_get = mocker.patch("jobless.scrapers.nayapay.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = NayaPayScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Creative Designer"
    assert first.company == "NayaPay"
    assert first.location == "Karachi"
    assert str(first.apply_link) == "https://www.nayapay.com/careers#creative-designer"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "DevOps Engineer"
    assert second.location == "Not specified"  # blank location on the page falls back cleanly
    assert str(second.apply_link) == "https://www.nayapay.com/careers#devops-engineer"


def test_scrape_returns_empty_list_when_no_cards_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.nayapay.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = NayaPayScraper().scrape()

    assert jobs == []
