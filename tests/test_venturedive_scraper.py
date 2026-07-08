from datetime import date

from jobless.scrapers.venturedive import VentureDiveScraper

CAREERS_PAGE_HTML = """
<html>
<body>
<resumator>
<div id="resumator-job-listings" class="resumator-job-listings resumator-jobs-text clrfix">
<table class="resumator-job-listings">
<tbody>
<tr class="resumator-job-heading">
    <th class="resumator-job-title-column">Job Title</th>
    <th class="resumator-department-column">Department</th>
    <th class="resumator-job-location-column">Location</th>
</tr>
<tr class="resumator-table-heading-row-even">
    <td class="resumator-table-heading-column" colspan="3"><span class="resumator-department-name">Architecture</span></td>
</tr>
<tr class="resumator-table-row-even">
    <td class="resumator-job-title-column"><a href="https://venturedive.applytojob.com/apply/6yA1hAbMr4/Senior-Data-AI-Architect" class="resumator-job-title-link">Senior Data &amp; AI Architect</a></td>
    <td class="resumator-department-column">Architecture</td>
    <td class="resumator-job-location-column">Karachi/ Lahore/ Islamabad, Pakistan</td>
</tr>
<tr class="resumator-table-heading-row-odd">
    <td class="resumator-table-heading-column" colspan="3"><span class="resumator-department-name">Internship</span></td>
</tr>
<tr class="resumator-table-row-odd">
    <td class="resumator-job-title-column"><a href="https://venturedive.applytojob.com/apply/DwoJdGtSz6/IT-Support-Intern" class="resumator-job-title-link">IT Support Intern</a></td>
    <td class="resumator-department-column">Internship</td>
    <td class="resumator-job-location-column">Lahore, Pakistan</td>
</tr>
</tbody>
</table>
</div>
</resumator>
</body>
</html>
"""


def test_scrape_parses_job_rows_from_static_html(mocker):
    mock_get = mocker.patch("jobless.scrapers.venturedive.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = VentureDiveScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Senior Data & AI Architect"
    assert first.company == "VentureDive"
    assert first.location == "Karachi/ Lahore/ Islamabad, Pakistan"
    assert (
        str(first.apply_link)
        == "https://venturedive.applytojob.com/apply/6yA1hAbMr4/Senior-Data-AI-Architect"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "IT Support Intern"
    assert second.company == "VentureDive"
    assert second.location == "Lahore, Pakistan"
    assert (
        str(second.apply_link)
        == "https://venturedive.applytojob.com/apply/DwoJdGtSz6/IT-Support-Intern"
    )


def test_scrape_returns_empty_list_when_listings_container_missing(mocker):
    mock_get = mocker.patch("jobless.scrapers.venturedive.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs widget here</body></html>", raise_for_status=lambda: None)

    jobs = VentureDiveScraper().scrape()

    assert jobs == []
