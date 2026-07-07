from datetime import date

from jobless.scrapers.codup import CodupScraper

CAREERS_PAGE_HTML = """
<html>
<body>
<main>
    <div class='job-board-list-wrapper'>
        <div class='jobs-list'>
            <h2 class='page-title page-title-open'>Current Openings</h2>
            <ul class='list-group'>
                <li class="list-group-item">
                    <h3 class='list-group-item-heading'>
                        <a href="https://codup.applytojob.com/apply/x6ynWgH0Uc/Admin-Executive">
                            Admin Executive
                        </a>
                    </h3>
                    <ul class='list-inline list-group-item-text'>
                        <li><i class='fa fa-map-marker'></i>Karachi, Sindh, Pakistan</li>
                    </ul>
                </li>
                <li class="list-group-item">
                    <h3 class='list-group-item-heading'>
                        <a href="https://codup.applytojob.com/apply/ChzQCIIAQ5/Golang-Developers-Full-Time-Contractual">
                            Golang Developers - Full time Contractual
                        </a>
                    </h3>
                    <ul class='list-inline list-group-item-text'>
                        <li><i class='fa fa-map-marker'></i>Remote</li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</main>
</body>
</html>
"""


def test_scrape_parses_job_list_from_static_html(mocker):
    mock_get = mocker.patch("jobless.scrapers.codup.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = CodupScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Admin Executive"
    assert first.company == "Codup"
    assert first.location == "Karachi, Sindh, Pakistan"
    assert str(first.apply_link) == "https://codup.applytojob.com/apply/x6ynWgH0Uc/Admin-Executive"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Golang Developers - Full time Contractual"
    assert second.location == "Remote"
    assert str(second.apply_link) == "https://codup.applytojob.com/apply/ChzQCIIAQ5/Golang-Developers-Full-Time-Contractual"
