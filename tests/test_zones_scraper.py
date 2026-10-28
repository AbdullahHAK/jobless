from datetime import date

from jobless.scrapers.zones import ZonesScraper

CAREERS_PAGE_HTML = """
<html><body>
<h3 class="h2">IT</h3>
<table class="jv-job-list">
<tbody>
  <tr>
    <td class="job-list-header">Job Title</td>
    <td class="job-list-header">Location</td>
  </tr>
  <tr onclick="location.href = '/zones/job/abc123'">
    <td class="jv-job-list-name">
      <a href="/zones/job/abc123">Principle Engineer</a>
    </td>
    <td class="jv-job-list-location">
      Islamabad,
      Pakistan
    </td>
    <td class="jv-job-list-req">24111</td>
  </tr>
  <tr onclick="location.href = '/zones/job/def456'">
    <td class="jv-job-list-name">
      <a href="/zones/job/def456">Manager Software Orchestration</a>
    </td>
    <td class="jv-job-list-location">
      Lahore, Pakistan
    </td>
    <td class="jv-job-list-req">24112</td>
  </tr>
</tbody>
</table>
<h3 class="h2">Field Sales</h3>
<table class="jv-job-list">
<tbody>
  <tr>
    <td class="job-list-header">Job Title</td>
    <td class="job-list-header">Location</td>
  </tr>
  <tr onclick="location.href = '/zones/job/ghi789'">
    <td class="jv-job-list-name">
      <a href="/zones/job/ghi789">Senior Sales Compensation Analyst</a>
    </td>
    <td class="jv-job-list-location">
      <div class="jv-meta">2 Locations</div>
    </td>
    <td class="jv-job-list-req">24113</td>
  </tr>
  <tr onclick="location.href = '/zones/job/jkl012'">
    <td class="jv-job-list-name">
      <a href="/zones/job/jkl012">National Sales Manager - Apple</a>
    </td>
    <td class="jv-job-list-location">
      Noida, India
    </td>
    <td class="jv-job-list-req">24114</td>
  </tr>
</tbody>
</table>
</body></html>
"""


def test_scrape_keeps_only_single_pakistan_location_postings(mocker):
    mock_get = mocker.patch("jobless.scrapers.zones.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = ZonesScraper().scrape()

    assert mock_get.call_count == 1
    # The ambiguous "2 Locations" row and the India-only row are excluded.
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Principle Engineer"
    assert first.company == "Zones"
    # Source HTML has "Islamabad,\n      Pakistan" across lines - must
    # collapse to one clean string, not keep the embedded newline/indent.
    assert first.location == "Islamabad, Pakistan"
    assert str(first.apply_link) == "https://jobs.jobvite.com/zones/job/abc123"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Manager Software Orchestration"
    assert second.location == "Lahore, Pakistan"


def test_scrape_returns_empty_list_when_no_postings_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.zones.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = ZonesScraper().scrape()

    assert jobs == []
