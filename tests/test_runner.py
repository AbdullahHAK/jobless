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


class _WorkingScraper:
    company_name = "CompanyA"

    def scrape(self):
        return [JOB_A]


class _FailingScraper:
    company_name = "CompanyB"

    def scrape(self):
        raise RuntimeError("site is down")


def test_run_all_reports_job_count_per_company_and_none_on_failure(mocker):
    mocker.patch(
        "jobless.runner.all_scrapers",
        return_value=[_WorkingScraper, _FailingScraper],
    )
    mocker.patch("jobless.runner.link_health.filter_live_jobs", side_effect=lambda jobs: jobs)

    jobs, results = runner.run_all()

    assert jobs == [JOB_A]
    assert results == {"CompanyA": 1, "CompanyB": None}  # CompanyB's scraper raised


def _patch_main_dependencies(mocker, get_scraper_health_return=None):
    mock_conn = mocker.MagicMock()
    mocker.patch("jobless.runner.db.get_connection", return_value=mock_conn)
    mock_close = mocker.patch("jobless.runner.db.close_stale_jobs", return_value=0)
    mocker.patch("jobless.runner.link_health.filter_live_jobs", side_effect=lambda jobs: jobs)
    mocker.patch("jobless.runner.db.get_scraper_health", return_value=get_scraper_health_return)
    mocker.patch("jobless.runner.db.upsert_scraper_health")
    mocker.patch("jobless.runner.alerts.send_email_summary")
    mocker.patch("jobless.runner.alerts.file_or_close_issue")
    return mock_conn, mock_close


def test_main_only_prunes_stale_jobs_for_a_company_whose_scraper_succeeded(mocker):
    mocker.patch("jobless.runner.all_scrapers", return_value=[_WorkingScraper, _FailingScraper])
    mock_conn, mock_close = _patch_main_dependencies(mocker)

    runner.main()

    # CompanyA scraped cleanly, so it's the only one ever pruned - CompanyB's
    # scraper raised, so its real listings must not be wiped out.
    mock_close.assert_called_once_with(mock_conn, "CompanyA", ["https://example.com/a/1"])


def test_main_skips_pruning_a_company_whose_job_count_anomalously_crashed(mocker):
    class _AlmostEmptyScraper:
        company_name = "CompanyA"

        def scrape(self):
            return []

    mocker.patch("jobless.runner.all_scrapers", return_value=[_AlmostEmptyScraper])
    # CompanyA had 40 jobs the last time its scraper ran cleanly - today it returned 0.
    _, mock_close = _patch_main_dependencies(
        mocker, get_scraper_health_return={"last_job_count": 40, "consecutive_issues": 0, "is_broken": False}
    )

    runner.main()

    # A crash from 40 to 0 looks like a broken scraper, not a company with
    # zero openings - its real listings must not be wiped out either.
    mock_close.assert_not_called()


def test_main_alerts_when_a_scraper_newly_crosses_the_broken_threshold(mocker):
    mocker.patch("jobless.runner.all_scrapers", return_value=[_WorkingScraper, _FailingScraper])
    _patch_main_dependencies(mocker)
    send_email_summary = mocker.patch("jobless.runner.alerts.send_email_summary")

    runner.main()

    # CompanyB's exception alerts on the very first occurrence (no debounce).
    newly_broken = send_email_summary.call_args[0][0]
    assert [h.company for h in newly_broken] == ["CompanyB"]
