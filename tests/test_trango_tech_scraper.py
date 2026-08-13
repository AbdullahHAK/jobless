from datetime import date

from jobless.scrapers.trango_tech import TrangoTechScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="trend-tabs">
  <div id="cross-plat-A" class="card tab-pane fade active show">
    <div class="area custom-job-area-careers">
      <button type="button" class="collapsible">
        <span class="txt-left">HRBP</span>
        <span class="txt-right">Karachi</span>
      </button>
      <div class="content">...</div>
      <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#exampleModal0">APPLY NOW</button>

      <button type="button" class="collapsible">
        <span class="txt-left">Wordpress Developer</span>
        <span class="txt-right">Lahore</span>
      </button>
      <div class="content">...</div>
      <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#exampleModal1">APPLY NOW</button>
    </div>
  </div>

  <div id="exampleModal0" class="modal fade">
    <iframe id="jobIframe" src="data:image/svg+xml,..." data-lzl-src="https://hrms.eplanetcom.com/Recruitment/Candidate/ApplyOnline?id=1489&amp;BranchId=4"></iframe>
  </div>
  <div id="exampleModal1" class="modal fade">
    <iframe id="jobIframe" src="data:image/svg+xml,..." data-lzl-src="https://hrms.eplanetcom.com/Recruitment/Candidate/ApplyOnline?id=1468&amp;BranchId=4"></iframe>
  </div>

  <!-- The site repeats the same job list in 3 more tabs (Function/Location/Experience) -
       only cross-plat-A should ever be parsed, so this duplicate must be ignored. -->
  <div id="cross-plat-B" class="card tab-pane fade">
    <div class="area custom-job-area-careers">
      <button type="button" class="collapsible">
        <span class="txt-left">HRBP</span>
        <span class="txt-right">Karachi</span>
      </button>
      <button type="button" class="btn" data-bs-toggle="modal" data-bs-target="#exampleModal0">APPLY NOW</button>
    </div>
  </div>
</div>
</body></html>
"""


def test_scrape_parses_only_the_first_tab_pane(mocker):
    mock_get = mocker.patch("jobless.scrapers.trango_tech.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = TrangoTechScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "HRBP"
    assert first.company == "Trango Tech"
    assert first.location == "Karachi"
    assert str(first.apply_link) == "https://hrms.eplanetcom.com/Recruitment/Candidate/ApplyOnline?id=1489&BranchId=4"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Wordpress Developer"
    assert second.location == "Lahore"
    assert str(second.apply_link) == "https://hrms.eplanetcom.com/Recruitment/Candidate/ApplyOnline?id=1468&BranchId=4"


def test_scrape_returns_empty_list_when_container_missing(mocker):
    mock_get = mocker.patch("jobless.scrapers.trango_tech.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = TrangoTechScraper().scrape()

    assert jobs == []
