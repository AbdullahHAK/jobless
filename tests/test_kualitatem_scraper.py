from datetime import date

from jobless.scrapers.kualitatem import KualitatemScraper

LISTING_HTML = """
<html><body>
<div class="container mt-5">
  <div class="row">
    <div class="col-md-4">
      <div class="job-card">
        <div class="job-title">Senior Test Engineer</div>
        <p class="job-positions">2 Open Position</p>
        <a href="https://new.careers.kualitatem.com/job/322" class="apply-btn">APPLY NOW</a>
      </div>
    </div>
    <div class="col-md-4">
      <div class="job-card">
        <div class="job-title">Associate AI/ML Engineer</div>
        <p class="job-positions">1 Open Position</p>
        <a href="https://new.careers.kualitatem.com/job/292" class="apply-btn">APPLY NOW</a>
      </div>
    </div>
  </div>
</div>
<div class="container mt-5">
  <div id="job-container" class="row">
    <!-- Single Job Layout (Hidden template, cloned for each job) -->
    <div class="col-md-4 job-template" style="display: none;">
      <div class="job-card">
        <div class="job-title">Job Title</div>
        <p class="job-positions">1 Open Position</p>
        <button class="apply-btn">APPLY NOW</button>
      </div>
    </div>
  </div>
</div>
</body></html>
"""

DETAIL_HTML_322 = """
<html><body>
<div class="job_details">
  <h1 class="job-title-description">Senior Test Engineer</h1>
  <ul class="job-info">
    <li><strong>Location:</strong> Bhutan &amp; India</li>
    <li><strong>Openings:</strong> 2</li>
    <li><strong>Salary Range:</strong> </li>
  </ul>
</div>
</body></html>
"""

DETAIL_HTML_292 = """
<html><body>
<div class="job_details">
  <h1 class="job-title-description">Associate AI/ML Engineer</h1>
  <ul class="job-info">
    <li><strong>Location:</strong> Lahore</li>
    <li><strong>Openings:</strong> 1</li>
    <li><strong>Salary Range:</strong> </li>
  </ul>
</div>
</body></html>
"""


def test_scrape_builds_job_schema_using_detail_page_for_location(mocker):
    mock_get = mocker.patch("jobless.scrapers.kualitatem.requests.get")
    mock_get.side_effect = [
        mocker.Mock(text=LISTING_HTML, raise_for_status=lambda: None),
        mocker.Mock(text=DETAIL_HTML_322, raise_for_status=lambda: None),
        mocker.Mock(text=DETAIL_HTML_292, raise_for_status=lambda: None),
    ]
    mock_sleep = mocker.patch("jobless.scrapers.kualitatem.time.sleep")

    jobs = KualitatemScraper().scrape()

    assert mock_get.call_count == 3
    # one listing fetch + two detail fetches, rate-limited between detail requests
    assert mock_sleep.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior Test Engineer"
    assert first.company == "Kualitatem"
    assert first.location == "Bhutan & India"
    assert str(first.apply_link) == "https://new.careers.kualitatem.com/job/322"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Associate AI/ML Engineer"
    assert second.location == "Lahore"
    assert str(second.apply_link) == "https://new.careers.kualitatem.com/job/292"


def test_scrape_falls_back_to_default_location_when_detail_page_fails(mocker):
    import requests

    mock_get = mocker.patch("jobless.scrapers.kualitatem.requests.get")

    def combined(url, headers=None, timeout=None):
        if url == "https://new.careers.kualitatem.com/":
            return mocker.Mock(text=LISTING_HTML, raise_for_status=lambda: None)
        if url == "https://new.careers.kualitatem.com/job/322":
            raise requests.RequestException("boom")
        return mocker.Mock(text=DETAIL_HTML_292, raise_for_status=lambda: None)

    mock_get.side_effect = combined
    mocker.patch("jobless.scrapers.kualitatem.time.sleep")

    jobs = KualitatemScraper().scrape()

    assert len(jobs) == 2
    assert jobs[0].location == "Not specified"
    assert jobs[1].location == "Lahore"
