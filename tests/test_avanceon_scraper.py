from datetime import date

from jobless.scrapers.avanceon import AvanceonScraper

CAREERS_PAGE_HTML = """
<html><body>
<ul class="positions location">
  <li class="position transition">
    <ul class="position-wrap">
      <li class="position-details flex-0">
        <a href="/p/6e8d255483a1-solution-architect-proposals" title="Apply">
          <h2>Solution Architect - Proposals</h2>
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
        <a href="/p/4755e917f901-project-engineer" title="Apply">
          <h2>Project Engineer (PLC/SCADA)</h2>
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
        <a href="/p/7402c673e2fe-design-and-proposal-lead" title="Apply">
          <h2>Design and Proposal Lead (Qatar Region)</h2>
          <ul class="meta">
            <li class="location"><i class="fa fa-map-marker"></i><span>Doha, QA</span>
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
        <a href="/p/6e8d255483a1-solution-architect-proposals" title="Apply">
          <h2>Solution Architect - Proposals</h2>
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


def test_scrape_keeps_only_pk_postings_and_dedupes_by_href(mocker):
    mock_get = mocker.patch("jobless.scrapers.avanceon.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = AvanceonScraper().scrape()

    assert mock_get.call_count == 1
    # The Qatar-only posting is excluded; the repeated Solution Architect
    # entry is deduped down to one.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Solution Architect - Proposals"
    assert first.company == "Avanceon"
    assert first.location == "Lahore, PK"
    assert str(first.apply_link) == "https://avanceon.breezy.hr/p/6e8d255483a1-solution-architect-proposals"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Project Engineer (PLC/SCADA)"
    assert second.location == "Karachi, PK"


def test_scrape_returns_empty_list_when_no_positions_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.avanceon.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = AvanceonScraper().scrape()

    assert jobs == []
