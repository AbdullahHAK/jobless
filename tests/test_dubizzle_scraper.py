from datetime import date

from jobless.scrapers.dubizzle import DubizzleScraper

CAREERS_PAGE_HTML = """
<html><body>
<ul class="positions location">
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/788e812f78ec01-principal-software-engineer-backend" title="Apply">
          <h2>Principal Software Engineer - Backend</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span class="polygot">%LABEL_MULTIPLE_LOCATIONS%</span><span> (2) </span>
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
        <a href="/p/f2e0f112cd3b01-principle-software-engineer-frontend" title="Apply">
          <h2>Principle Software Engineer (Frontend)</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Karachi, PK</span>
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
        <a href="/p/c80c266fc34a01-accounts-officer" title="Apply">
          <h2>Accounts Officer</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Lahore, PK</span>
              <li class="type"><span class="polygot">%LABEL_POSITION_TYPE_FULL_TIME%</span></li>
            </li>
          </ul>
        </a>
      </li>
    </ul>
  </li>
  <!-- Same posting repeated under a per-location grouping further down
       the real page - must be deduped by href, not counted twice. -->
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/788e812f78ec01-principal-software-engineer-backend" title="Apply">
          <h2>Principal Software Engineer - Backend</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span class="polygot">%LABEL_MULTIPLE_LOCATIONS%</span><span> (2) </span>
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


def test_scrape_keeps_only_single_pakistan_city_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.dubizzle.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = DubizzleScraper().scrape()

    assert mock_get.call_count == 1
    # The multi-location "Principal Software Engineer - Backend" posting is
    # excluded (can't resolve which cities from "%LABEL_MULTIPLE_LOCATIONS%"
    # alone), leaving the two single-city postings.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Principle Software Engineer (Frontend)"
    assert first.company == "Dubizzle"
    assert first.location == "Karachi, PK"
    assert (
        str(first.apply_link)
        == "https://dubizzlelabs.breezy.hr/p/f2e0f112cd3b01-principle-software-engineer-frontend"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Accounts Officer"
    assert second.location == "Lahore, PK"


def test_scrape_returns_empty_list_when_no_positions_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.dubizzle.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = DubizzleScraper().scrape()

    assert jobs == []
