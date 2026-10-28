from datetime import date

from jobless.scrapers.zameen import ZameenScraper

CAREERS_PAGE_HTML = """
<html><body>
<ul class="positions location">
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/001deb999c1501-field-sales-expert-pharma" title="Apply">
          <h2>Field Sales Expert - pharma</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Faisalabad, PK</span>
              <li class="type"><span class="polygot">%LABEL_POSITION_TYPE_FULL_TIME%</span></li>
            </li>
          </ul>
        </a>
      </li>
    </ul>
  </li>
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/a1b2c3d4-qaqc-engineer" title="Apply">
          <h2>QAQC Engineer</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Lahore, PK</span>
              <li class="type"><span class="polygot">%LABEL_POSITION_TYPE_FULL_TIME%</span></li>
            </li>
          </ul>
        </a>
      </li>
    </ul>
  </li>
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/e5f6-remote-sales-consultant" title="Apply">
          <h2>Remote Sales Consultant (Dubai Region)</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Dubai, AE</span>
              <li class="type"><span class="polygot">%LABEL_POSITION_TYPE_FULL_TIME%</span></li>
            </li>
          </ul>
        </a>
      </li>
    </ul>
  </li>
</ul>
</body></html>
"""


def test_scrape_keeps_only_pk_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.zameen.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = ZameenScraper().scrape()

    assert mock_get.call_count == 1
    # The Dubai-only posting is excluded.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Field Sales Expert - pharma"
    assert first.company == "Zameen.com"
    assert first.location == "Faisalabad, PK"
    assert str(first.apply_link) == "https://zameen.breezy.hr/p/001deb999c1501-field-sales-expert-pharma"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "QAQC Engineer"
    assert second.location == "Lahore, PK"


def test_scrape_returns_empty_list_when_no_positions_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.zameen.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = ZameenScraper().scrape()

    assert jobs == []
