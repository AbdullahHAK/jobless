from datetime import date

from jobless.scrapers.sadapay import SadaPayScraper

CAREERS_PAGE_HTML = """
<html><body>
<a href="/jobs-listing/ai-first-product-designer" class="job-wrap w-inline-block">
  <div class="job-wrapper">
    <div class="heading-job-wrap">
      <div class="job-title"><h1 class="heading-medium job-heading">AI-First Product Designer</h1></div>
    </div>
    <div class="job-feature">
      <div class="job-location"><p class="paragraph-4">Karachi, Lahore, Islamabad</p></div>
    </div>
  </div>
</a>
<a href="/jobs-listing/data-engineer" class="job-wrap w-inline-block">
  <div class="job-wrapper">
    <div class="heading-job-wrap">
      <div class="job-title"><h1 class="heading-medium job-heading">Data Engineer</h1></div>
    </div>
    <div class="job-feature">
      <div class="job-location"><p class="paragraph-4">Karachi</p></div>
    </div>
  </div>
</a>
</body></html>
"""


def test_scrape_returns_real_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.sadapay.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = SadaPayScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "AI-First Product Designer"
    assert first.company == "SadaPay"
    assert first.location == "Karachi, Lahore, Islamabad"
    assert str(first.apply_link) == "https://sadapay.pk/jobs-listing/ai-first-product-designer"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Data Engineer"
    assert second.location == "Karachi"


def test_scrape_returns_empty_list_when_no_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.sadapay.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = SadaPayScraper().scrape()

    assert jobs == []
