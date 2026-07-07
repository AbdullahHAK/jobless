from datetime import date

from jobless.scrapers.folio3 import Folio3Scraper

CAREERS_PAGE_HTML = """
<html>
<body>
<div class="jobs-section-accordion acc">
    <div class='jobs-box acc__card' data-tags='' data-title='senior software engineer (golang)' data-division='App Dev' data-location='Pakistan' data-type='Regular' data-remote='false'>
        <div class='job-header active-accordian'>
            <h1 class='acc__title'>Senior Software Engineer (GoLang)</h1>
            <div class='head-pills'>
                <div class='col-left'>
                    <span>Pakistan</span>
                    <h3>Regular</h3>
                </div>
                <div class='col-right'>
                    <p class='apply-btn'><a href='https://folio3.com/jobs/senior-software-engineer-golang/'>Apply Now</a></p>
                </div>
            </div>
        </div>
        <div class='acc__panel'>
            <p>We are looking for a Senior Software Engineer with strong GoLang experience.</p>
        </div>
    </div>
    <div class='jobs-box acc__card' data-tags='' data-title='marketing intern' data-division='Marketing' data-location='Pakistan' data-type='Regular' data-remote='false'>
        <div class='job-header'>
            <h1 class='acc__title'>Marketing Intern</h1>
            <div class='head-pills'>
                <div class='col-left'>
                    <span>Pakistan</span>
                    <h3>Regular</h3>
                </div>
                <div class='col-right'>
                    <p class='apply-btn'><a href='https://folio3.com/jobs/marketing-intern-3/'>Apply Now</a></p>
                </div>
            </div>
        </div>
        <div class='acc__panel'>
            <p>Folio3 is looking for a Marketing Intern to join the team.</p>
        </div>
    </div>
</div>
</body>
</html>
"""


def test_scrape_parses_job_cards_from_static_html(mocker):
    mock_get = mocker.patch("jobless.scrapers.folio3.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = Folio3Scraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior Software Engineer (GoLang)"
    assert first.company == "Folio3"
    assert first.location == "Pakistan"
    assert str(first.apply_link) == "https://folio3.com/jobs/senior-software-engineer-golang/"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Marketing Intern"
    assert second.company == "Folio3"
    assert str(second.apply_link) == "https://folio3.com/jobs/marketing-intern-3/"
