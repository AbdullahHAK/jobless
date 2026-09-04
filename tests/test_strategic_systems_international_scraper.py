from datetime import date

from jobless.scrapers.strategic_systems_international import StrategicSystemsInternationalScraper

CAREERS_PAGE_HTML = """
<html><body>
<ul class="positions location">
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/588736b4c73e-business-data-analyst" title="Apply">
          <h2>Business/Data Analyst</h2>
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
        <a href="/p/01945e70e3a5-ai-security-engineer" title="Apply">
          <h2>AI Security Engineer (AI &amp; Agentic Security)</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span class="polygot">%LABEL_MULTIPLE_LOCATIONS%</span><span> (5) </span>
              <li class="type"><span class="polygot">%LABEL_POSITION_TYPE_CONTRACT%</span></li>
            </li>
          </ul>
        </a>
      </li>
    </ul>
  </li>
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/b5eb1bd1cfcc-software-architect" title="Apply">
          <h2>Software Architect</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Lahore, PK</span>
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


def test_scrape_keeps_only_single_lahore_location_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.strategic_systems_international.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = StrategicSystemsInternationalScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the multi-location AI Security Engineer posting must be excluded

    first = jobs[0]
    assert first.title == "Business/Data Analyst"
    assert first.company == "Strategic Systems International"
    assert first.location == "Lahore, PK"
    assert (
        str(first.apply_link)
        == "https://strategic-systems-international.breezy.hr/p/588736b4c73e-business-data-analyst"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Software Architect"


def test_scrape_returns_empty_list_when_no_positions_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.strategic_systems_international.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = StrategicSystemsInternationalScraper().scrape()

    assert jobs == []
