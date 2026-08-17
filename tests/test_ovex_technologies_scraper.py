from datetime import date

from jobless.scrapers.ovex_technologies import OvexTechnologiesScraper

CAREERS_PAGE_HTML = """
<html><body>
<section class="open-positions">
  <h2>Open Positions</h2>
  <div class="approach-details ad_c">
    <div class="box">
      <h4 class="head">CSR (Outbound) - Call Center</h4>
      <p class="desc">We are seeking motivated and customer-oriented Call Centre Representatives...</p>
      <p class="desc"><b>Location: Lahore </b></p>
      <a href="https://www.ovextech.com/jobDetail/Vm0xMFlWbFdTbkpQVm1SU1lrVndVbFpyVWtKUFVUMDk=" class="more-btn">Apply</a>
    </div>
    <div class="box">
      <h4 class="head">Senior IT Support Specialist - Islamabad</h4>
      <p class="desc">Looking for an experienced IT support specialist...</p>
      <p class="desc"><b>Location: Lahore </b></p>
      <a href="https://www.ovextech.com/jobDetail/Vm0xMFlXRXlSbkpQVm1SU1lrVndVbFpyVWtKUFVUMDk=" class="more-btn">Apply</a>
    </div>
  </div>
</section>
</body></html>
"""


def test_scrape_parses_job_boxes(mocker):
    mock_get = mocker.patch("jobless.scrapers.ovex_technologies.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = OvexTechnologiesScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "CSR (Outbound) - Call Center"
    assert first.company == "Ovex Technologies"
    assert first.location == "Lahore"
    assert (
        str(first.apply_link)
        == "https://www.ovextech.com/jobDetail/Vm0xMFlWbFdTbkpQVm1SU1lrVndVbFpyVWtKUFVUMDk="
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior IT Support Specialist - Islamabad"
    assert second.location == "Lahore"


def test_scrape_returns_empty_list_when_no_boxes_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.ovex_technologies.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = OvexTechnologiesScraper().scrape()

    assert jobs == []
