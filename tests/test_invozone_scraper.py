from datetime import date

from jobless.scrapers.invozone import InvoZoneScraper

PAGE_ONE_HTML = """
<html><body>
<div class="row">
  <div class="mb-8 col-sm-6">
    <div id="it-administrator-1783420700985-61jgtj" name="card" class="card border h-100" role="button">
      <div class="p-6">
        <h4 class="mt-0 mb-1 jobs-page text-truncate" title="IT Administrator">IT Administrator</h4>
        <div class="text-14">
          <div class="mt-3 flex align-items-center">
            <svg class="icon"><use href="#icon-branch"></use></svg>
            Admin Operations - IZ
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="mb-8 col-sm-6">
    <div id="jobs/invozone/cold-caller" name="card" class="card border h-100" role="button">
      <div class="p-6">
        <h4 class="mt-0 mb-1 jobs-page text-truncate" title="Cold Caller">Cold Caller</h4>
        <div class="text-14">
          <div class="mt-3 flex align-items-center">
            <svg class="icon"><path d="M1 1"></path></svg>
            Lahore
          </div>
          <div class="mt-3 flex align-items-center">
            <svg class="icon"><use href="#icon-branch"></use></svg>
            Sales
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</body></html>
"""

EMPTY_PAGE_HTML = """
<html><body><p class="text-secondary mb-4 text-15">Showing 0 results</p></body></html>
"""


def test_scrape_stops_at_empty_page_and_builds_job_schema(mocker):
    mock_get = mocker.patch("jobless.scrapers.invozone.requests.get")
    mock_get.side_effect = [
        mocker.Mock(text=PAGE_ONE_HTML, raise_for_status=lambda: None),
        mocker.Mock(text=EMPTY_PAGE_HTML, raise_for_status=lambda: None),
    ]
    mocker.patch("jobless.scrapers.invozone.time.sleep")

    jobs = InvoZoneScraper().scrape()

    assert mock_get.call_count == 2
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "IT Administrator"
    assert first.company == "InvoZone"
    assert first.location == "Not specified"
    assert str(first.apply_link) == "https://next.invozone.com/it-administrator-1783420700985-61jgtj"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Cold Caller"
    assert second.location == "Lahore"
    assert str(second.apply_link) == "https://next.invozone.com/jobs/invozone/cold-caller"
