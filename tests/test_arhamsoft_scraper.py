from datetime import date

from jobless.scrapers.arhamsoft import ArhamSoftScraper

LIST_PAGE_HTML = """
<html><body>
<div class="group">
  <h3 class="mini-sub-heading">
    <a href="/careers/aaa111">SQA Engineer - Manual &amp; Automation Testing</a>
  </h3>
</div>
<div class="group">
  <h3 class="mini-sub-heading">
    <a href="/careers/bbb222">Business Development Executive</a>
  </h3>
</div>
</body></html>
"""

PK_DETAIL_HTML = """
<html><body>
<dl>
  <div><dt>Date Opened</dt><dd>Sep 15, 2026</dd></div>
  <div><dt>Job Type</dt><dd>On-site</dd></div>
  <div><dt>City</dt><dd>Lahore</dd></div>
  <div><dt>Country</dt><dd>Pakistan</dd></div>
  <div><dt>Zip / Postal Code</dt><dd>54000</dd></div>
</dl>
</body></html>
"""

US_DETAIL_HTML = """
<html><body>
<dl>
  <div><dt>City</dt><dd>New York</dd></div>
  <div><dt>Country</dt><dd>United States</dd></div>
</dl>
</body></html>
"""


def test_scrape_keeps_only_pakistan_located_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.arhamsoft.requests.get")
    mock_get.side_effect = [
        mocker.Mock(text=LIST_PAGE_HTML, raise_for_status=lambda: None),
        mocker.Mock(text=PK_DETAIL_HTML, raise_for_status=lambda: None),
        mocker.Mock(text=US_DETAIL_HTML, raise_for_status=lambda: None),
    ]

    jobs = ArhamSoftScraper().scrape()

    assert mock_get.call_count == 3
    assert len(jobs) == 1

    job = jobs[0]
    assert job.title == "SQA Engineer - Manual & Automation Testing"
    assert job.company == "ArhamSoft"
    assert job.location == "Lahore, Pakistan"
    assert str(job.apply_link) == "https://career.arhamsoft.com/careers/aaa111"
    assert job.date_scraped == date.today()


def test_scrape_returns_empty_list_when_no_postings_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.arhamsoft.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = ArhamSoftScraper().scrape()

    assert jobs == []
