from datetime import date

from jobless.scrapers.tkxel import TkxelScraper

CAREERS_PAGE_HTML = """
<html>
<body>
<div class="jobs-cards-wrp">
    <div class="job-card">
        <a href="https://jobs.tkxel.com/jobs/Careers/524295000041422528/SCADA-Developer-Consultant?source=CareerSite">
            <div class="job-title"><h6>SCADA Developer/Consultant</h6> <svg width="12" height="11"></svg></div>
            <div class="job-location"><p>N/A</p></div>
        </a>
    </div>
    <div class="job-card">
        <a href="https://jobs.tkxel.com/jobs/Careers/524295000041154584/Senior-Database-Engineer?source=CareerSite">
            <div class="job-title"><h6>Senior Database Engineer</h6> <svg width="12" height="11"></svg></div>
            <div class="job-location"><p>Lahore, Pakistan</p></div>
        </a>
    </div>
</div>
</body>
</html>
"""


def test_scrape_parses_job_cards_from_static_html(mocker):
    mock_get = mocker.patch("jobless.scrapers.tkxel.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = TkxelScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "SCADA Developer/Consultant"
    assert first.company == "Tkxel"
    assert first.location == "N/A"
    assert (
        str(first.apply_link)
        == "https://jobs.tkxel.com/jobs/Careers/524295000041422528/SCADA-Developer-Consultant?source=CareerSite"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior Database Engineer"
    assert second.company == "Tkxel"
    assert second.location == "Lahore, Pakistan"
    assert (
        str(second.apply_link)
        == "https://jobs.tkxel.com/jobs/Careers/524295000041154584/Senior-Database-Engineer?source=CareerSite"
    )
