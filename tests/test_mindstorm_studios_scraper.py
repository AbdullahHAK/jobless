from datetime import date

from jobless.scrapers.mindstorm_studios import MindstormStudiosScraper

CAREERS_PAGE_HTML = """
<html><body>
<div class="featured-jobs">
  <a class="list-group-item" id="featured_59156" href="//mindstormstudios.simplicant.com/jobs/59156-3d-game-artist-advertising/detail">
    <h3 class="list-group-item-title job-title">3D Game Artist (Advertising)</h3>
    <div class="list-group-item-subtitle job-subtitle">Lahore, Pakistan</div>
  </a>
</div>

<h2 class="heading">Art</h2>
<div class="list-group list-jobs">
  <a class="list-group-item" id="59156_job_link" href="//mindstormstudios.simplicant.com/jobs/59156-3d-game-artist-advertising/detail">
    <h3 class="list-group-item-title job-title">3D Game Artist (Advertising)</h3>
    <div class="list-group-item-subtitle job-subtitle">Lahore, Pakistan</div>
  </a>
</div>

<h2 class="heading">Engineering</h2>
<div class="list-group list-jobs">
  <a class="list-group-item" id="39590_job_link" href="//mindstormstudios.simplicant.com/jobs/39590-senior-game-developer/detail">
    <h3 class="list-group-item-title job-title">Senior Game Developer</h3>
    <div class="list-group-item-subtitle job-subtitle">Lahore, Pakistan</div>
  </a>
</div>
</body></html>
"""


def test_scrape_dedupes_the_featured_and_department_copies(mocker):
    mock_get = mocker.patch("jobless.scrapers.mindstorm_studios.requests.get")
    mock_get.return_value = mocker.Mock(text=CAREERS_PAGE_HTML, raise_for_status=lambda: None)

    jobs = MindstormStudiosScraper().scrape()

    assert mock_get.call_count == 1
    assert len(jobs) == 2  # the featured-carousel copy of the 3D Game Artist role must not duplicate

    first = jobs[0]
    assert first.title == "3D Game Artist (Advertising)"
    assert first.company == "Mindstorm Studios"
    assert first.location == "Lahore, Pakistan"
    assert (
        str(first.apply_link)
        == "https://mindstormstudios.simplicant.com/jobs/59156-3d-game-artist-advertising/detail"
    )
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "Senior Game Developer"


def test_scrape_returns_empty_list_when_no_job_links_present(mocker):
    mock_get = mocker.patch("jobless.scrapers.mindstorm_studios.requests.get")
    mock_get.return_value = mocker.Mock(text="<html><body>No jobs here</body></html>", raise_for_status=lambda: None)

    jobs = MindstormStudiosScraper().scrape()

    assert jobs == []
