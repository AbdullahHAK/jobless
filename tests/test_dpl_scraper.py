from datetime import date

from jobless.scrapers.dpl import DPLScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="tab-content">
  <div class="tab-pane fade in active" id="alljobs">
    <ul class="career-jobs-grid">
      <li>
        <article class="career-job-card">
          <a href="https://dplit.zohorecruit.com/jobs/Careers/651851000023884450?source=CareerSite"
             class="career-job-card__title">Full Stack .NET Developer</a>
          <div class="career-job-card__meta-item">
            <span class="career-job-card__meta-label">City</span>
            <span class="career-job-card__meta-value">Islamabad</span>
          </div>
        </article>
      </li>
      <li>
        <article class="career-job-card">
          <a href="https://dplit.zohorecruit.com/jobs/Careers/651851000023591330?source=CareerSite"
             class="career-job-card__title">QA Engineer</a>
          <div class="career-job-card__meta-item">
            <span class="career-job-card__meta-label">City</span>
            <span class="career-job-card__meta-value">Islamabad</span>
          </div>
        </article>
      </li>
    </ul>
  </div>

  <!-- The site repeats each card again under per-city filter tabs - only
       #alljobs should ever be parsed, so this duplicate must be ignored. -->
  <div class="tab-pane fade" id="islamabadjobs">
    <ul class="career-jobs-grid">
      <li>
        <article class="career-job-card">
          <a href="https://dplit.zohorecruit.com/jobs/Careers/651851000023884450?source=CareerSite"
             class="career-job-card__title">Full Stack .NET Developer</a>
          <div class="career-job-card__meta-item">
            <span class="career-job-card__meta-label">City</span>
            <span class="career-job-card__meta-value">Islamabad</span>
          </div>
        </article>
      </li>
    </ul>
  </div>
</div>
</body></html>
"""


def test_scrape_parses_only_the_alljobs_tab(mocker):
    mock_get = mocker.patch("jobless.scrapers.dpl.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = DPLScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Full Stack .NET Developer"
    assert first.company == "DPL"
    assert first.location == "Islamabad"
    assert str(first.apply_link) == "https://dplit.zohorecruit.com/jobs/Careers/651851000023884450?source=CareerSite"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "QA Engineer"
    assert str(second.apply_link) == "https://dplit.zohorecruit.com/jobs/Careers/651851000023591330?source=CareerSite"


def test_scrape_returns_empty_list_when_alljobs_tab_missing(mocker):
    mock_get = mocker.patch("jobless.scrapers.dpl.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = DPLScraper().scrape()

    assert jobs == []
