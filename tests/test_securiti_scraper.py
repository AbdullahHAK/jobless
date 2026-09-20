import logging
from datetime import date

from jobless.scrapers.securiti import SecuritiScraper

CAREERS_PAGE_HTML = """
<html><body>
<a href="/job/san-jose/senior-forward-deployed-engineer/22681/100820734912">Featured job outside the results list</a>
<section id="search-results" data-total-results="3" data-total-pages="{pages}" data-current-page="1">
  <div id="search-results-list">
    <ul>
      <li>
        <a data-job-id="94717080672" href="/job/islamabad/technical-writer/22681/94717080672">
          <h2 class="job-list__title">Technical Writer</h2>
          <span class="job-list__category">Securiti AI</span>
          <span class="job-list__location">Islamabad, Islamabad</span>
        </a>
        <button class="js-save-job-btn">Save for Later</button>
      </li>
      <li>
        <a data-job-id="99387071552" href="/job/karachi/senior-sdet/22681/99387071552">
          <h2 class="job-list__title">Senior SDET</h2>
          <span class="job-list__category">Securiti AI</span>
          <span class="job-list__location">Karachi, Sindh</span>
        </a>
      </li>
    </ul>
  </div>
</section>
</body></html>
"""


def _mock_page(mocker, html):
    mock_get = mocker.patch("jobless.scrapers.securiti.requests.get")
    mock_get.return_value = mocker.Mock(text=html, raise_for_status=lambda: None)
    return mock_get


def test_scrape_parses_results_and_cleans_duplicate_location(mocker):
    mock_get = _mock_page(mocker, CAREERS_PAGE_HTML.format(pages=1))

    jobs = SecuritiScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the featured link outside #search-results-list must be ignored

    first = jobs[0]
    assert first.title == "Technical Writer"
    assert first.company == "Securiti (Veeam)"
    assert first.location == "Islamabad"  # "Islamabad, Islamabad" collapsed
    assert str(first.apply_link) == "https://careers.veeam.com/job/islamabad/technical-writer/22681/94717080672"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior SDET"
    assert second.location == "Karachi, Sindh"  # distinct parts are kept


def test_scrape_warns_when_results_span_multiple_pages(mocker, caplog):
    _mock_page(mocker, CAREERS_PAGE_HTML.format(pages=3))

    with caplog.at_level(logging.WARNING, logger="jobless.scrapers.securiti"):
        jobs = SecuritiScraper().scrape()

    assert len(jobs) == 2  # still returns what page 1 had
    assert any("only the first page is scraped" in record.message for record in caplog.records)


def test_scrape_returns_empty_list_when_no_results(mocker):
    _mock_page(mocker, "<html><body>No jobs here</body></html>")

    jobs = SecuritiScraper().scrape()

    assert jobs == []
