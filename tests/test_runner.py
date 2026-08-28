from datetime import date

from jobless import runner
from jobless.scrapers.base import Job

JOB_A = Job(
    title="Software Engineer",
    company="CompanyA",
    location="Lahore",
    apply_link="https://example.com/a/1",
    date_scraped=date.today(),
)
JOB_B = Job(
    title="QA Engineer",
    company="CompanyB",
    location="Karachi",
    apply_link="https://example.com/b/1",
    date_scraped=date.today(),
)


class _WorkingScraper:
    company_name = "CompanyA"

    def scrape(self):
        return [JOB_A]


class _FailingScraper:
    company_name = "CompanyB"

    def scrape(self):
        raise RuntimeError("site is down")


def test_run_all_tracks_only_companies_whose_scraper_succeeded(mocker):
    mocker.patch(
        "jobless.runner.all_scrapers",
        return_value=[_WorkingScraper, _FailingScraper],
    )

    jobs, succeeded = runner.run_all()

    assert jobs == [JOB_A]
    assert succeeded == {"CompanyA"}  # CompanyB failed, so it must not be in the succeeded set


def test_main_only_prunes_stale_jobs_for_companies_that_succeeded(mocker):
    mocker.patch(
        "jobless.runner.all_scrapers",
        return_value=[_WorkingScraper, _FailingScraper],
    )
    mock_conn = mocker.MagicMock()
    mocker.patch("jobless.runner.db.get_connection", return_value=mock_conn)
    mock_close = mocker.patch("jobless.runner.db.close_stale_jobs", return_value=0)

    runner.main()

    # Only CompanyA's scraper succeeded, so only CompanyA should ever be pruned -
    # CompanyB's real listings must not be wiped out just because its scraper failed.
    mock_close.assert_called_once_with(mock_conn, "CompanyA", ["https://example.com/a/1"])
