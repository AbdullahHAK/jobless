from jobless import scraper_health


def test_evaluate_treats_first_ever_run_with_zero_jobs_as_healthy(mocker):
    mocker.patch("jobless.scraper_health.db.get_scraper_health", return_value=None)
    upsert = mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "NewCo", 0)

    assert result.issue is None
    assert result.should_skip_close is False
    assert result.should_alert is False
    upsert.assert_called_once_with(conn, "NewCo", last_job_count=0, consecutive_issues=0, is_broken=False)


def test_evaluate_flags_an_exception_as_broken_immediately(mocker):
    mocker.patch("jobless.scraper_health.db.get_scraper_health", return_value=None)
    mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "CompanyA", None)

    assert result.issue == "exception"
    assert result.should_skip_close is True
    assert result.should_alert is True  # alerts on the very first exception, no debounce


def test_evaluate_does_not_alert_on_a_single_anomalous_drop(mocker):
    mocker.patch(
        "jobless.scraper_health.db.get_scraper_health",
        return_value={"last_job_count": 40, "consecutive_issues": 0, "is_broken": False},
    )
    upsert = mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "CompanyA", 0)

    assert result.issue == "anomaly"
    assert result.should_skip_close is True  # never closes stale jobs on an anomalous run...
    assert result.should_alert is False  # ...but only alerts after a 2nd consecutive one
    upsert.assert_called_once_with(conn, "CompanyA", last_job_count=40, consecutive_issues=1, is_broken=False)


def test_evaluate_alerts_on_the_second_consecutive_anomalous_drop(mocker):
    mocker.patch(
        "jobless.scraper_health.db.get_scraper_health",
        return_value={"last_job_count": 40, "consecutive_issues": 1, "is_broken": False},
    )
    mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "CompanyA", 0)

    assert result.should_alert is True
    assert result.consecutive_issues == 2


def test_evaluate_does_not_re_alert_while_already_broken(mocker):
    mocker.patch(
        "jobless.scraper_health.db.get_scraper_health",
        return_value={"last_job_count": 40, "consecutive_issues": 2, "is_broken": True},
    )
    mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "CompanyA", 0)

    assert result.should_alert is False  # already flagged broken - don't re-alert every day it stays that way


def test_evaluate_reports_recovery_when_a_broken_scraper_returns_to_normal(mocker):
    mocker.patch(
        "jobless.scraper_health.db.get_scraper_health",
        return_value={"last_job_count": 40, "consecutive_issues": 3, "is_broken": True},
    )
    upsert = mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "CompanyA", 38)

    assert result.issue is None
    assert result.is_recovery is True
    assert result.should_skip_close is False  # back to normal - safe to prune stale jobs again
    upsert.assert_called_once_with(conn, "CompanyA", last_job_count=38, consecutive_issues=0, is_broken=False)


def test_evaluate_exempts_small_boards_from_the_ratio_check(mocker):
    # 2 -> 1 is a >50% drop by ratio, but boards this small aren't held to
    # the ratio rule - only an outright drop to zero counts as suspicious.
    mocker.patch(
        "jobless.scraper_health.db.get_scraper_health",
        return_value={"last_job_count": 2, "consecutive_issues": 0, "is_broken": False},
    )
    mocker.patch("jobless.scraper_health.db.upsert_scraper_health")
    conn = mocker.MagicMock()

    result = scraper_health.evaluate(conn, "TinyCo", 1)

    assert result.issue is None
