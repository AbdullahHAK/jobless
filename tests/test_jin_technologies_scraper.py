from datetime import date

from jobless.scrapers.jin_technologies import JinTechnologiesScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="vc_row wpb_row">
  <div class="wpb_wrapper">
    <h4>Are you interested in becoming a part of our team? Explore the
    current vacancies available:</h4>
  </div>
</div>
<div class="vc_row wpb_row">
  <div class="wpb_column vc_column_container vc_col-md-4">
    <div class="vc_column-inner"><div class="wpb_wrapper">
      <h5>Islamabad</h5>
      <p><a href="https://jintech.com/software-engineer/"><strong>Software Engineer</strong></a></p>
      <p><em>October 28, 2026</em></p>
      <p><a href="https://jintech.com/human-resources-officer/"><strong>Human Resources Officer</strong></a></p>
      <p><em>October 28, 2026</em></p>
    </div></div>
  </div>
  <div class="wpb_column vc_column_container vc_col-md-4">
    <div class="vc_column-inner"><div class="wpb_wrapper">
      <h5>Karachi</h5>
      <p>We don't have any open positions at the moment. Please check back soon.</p>
    </div></div>
  </div>
  <div class="wpb_column vc_column_container vc_col-md-4">
    <div class="vc_column-inner"><div class="wpb_wrapper">
      <h5>Multan</h5>
      <p>We don't have any open positions at the moment. Please check back soon.</p>
    </div></div>
  </div>
</div>
</body></html>
"""


def test_scrape_parses_jobs_from_the_city_grid(mocker):
    mock_get = mocker.patch("jobless.scrapers.jin_technologies.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = JinTechnologiesScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Software Engineer"
    assert first.company == "Jin Technologies"
    assert first.location == "Islamabad, Pakistan"
    assert str(first.apply_link) == "https://jintech.com/software-engineer/"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Human Resources Officer"
    assert second.location == "Islamabad, Pakistan"


def test_scrape_returns_empty_list_when_no_cities_have_openings(mocker):
    html = """
    <html><body>
    <div class="vc_row wpb_row"><div class="wpb_wrapper">
      <h4>current vacancies available:</h4>
    </div></div>
    <div class="vc_row wpb_row">
      <div class="wpb_column vc_column_container">
        <div class="vc_column-inner"><div class="wpb_wrapper">
          <h5>Karachi</h5>
          <p>We don't have any open positions at the moment.</p>
        </div></div>
      </div>
    </div>
    </body></html>
    """
    mock_get = mocker.patch("jobless.scrapers.jin_technologies.requests.get")
    mock_get.return_value = mocker.Mock(text=html, raise_for_status=lambda: None)

    jobs = JinTechnologiesScraper().scrape()

    assert jobs == []
