import requests

from jobless import alerts
from jobless.scraper_health import HealthResult

BROKEN = HealthResult(
    company="CompanyA",
    issue="exception",
    should_skip_close=True,
    should_alert=True,
    is_recovery=False,
    consecutive_issues=1,
    job_count=None,
)

RECOVERED = HealthResult(
    company="CompanyA",
    issue=None,
    should_skip_close=False,
    should_alert=False,
    is_recovery=True,
    consecutive_issues=0,
    job_count=38,
)


def test_file_or_close_issue_does_nothing_without_github_token(mocker, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", "AbdullahHAK/jobless")
    mock_get = mocker.patch("jobless.alerts.requests.get")

    alerts.file_or_close_issue(BROKEN)

    mock_get.assert_not_called()


def test_file_or_close_issue_files_a_new_issue_when_none_exists(mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "AbdullahHAK/jobless")
    mocker.patch(
        "jobless.alerts.requests.get",
        return_value=mocker.Mock(json=lambda: [], raise_for_status=lambda: None),
    )
    mock_post = mocker.patch("jobless.alerts.requests.post", return_value=mocker.Mock(raise_for_status=lambda: None))

    alerts.file_or_close_issue(BROKEN)

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["title"] == "Scraper broken: CompanyA"
    assert kwargs["json"]["labels"] == ["scraper-broken"]


def test_file_or_close_issue_skips_filing_a_duplicate(mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "AbdullahHAK/jobless")
    existing = [{"title": "Scraper broken: CompanyA", "number": 42}]
    mocker.patch(
        "jobless.alerts.requests.get",
        return_value=mocker.Mock(json=lambda: existing, raise_for_status=lambda: None),
    )
    mock_post = mocker.patch("jobless.alerts.requests.post")

    alerts.file_or_close_issue(BROKEN)

    mock_post.assert_not_called()


def test_file_or_close_issue_closes_the_issue_on_recovery(mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "AbdullahHAK/jobless")
    existing = [{"title": "Scraper broken: CompanyA", "number": 42}]
    mocker.patch(
        "jobless.alerts.requests.get",
        return_value=mocker.Mock(json=lambda: existing, raise_for_status=lambda: None),
    )
    mock_patch = mocker.patch("jobless.alerts.requests.patch", return_value=mocker.Mock(raise_for_status=lambda: None))

    alerts.file_or_close_issue(RECOVERED)

    mock_patch.assert_called_once()
    args, kwargs = mock_patch.call_args
    assert args[0].endswith("/issues/42")
    assert kwargs["json"] == {"state": "closed"}


def test_file_or_close_issue_swallows_request_errors(mocker, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "AbdullahHAK/jobless")
    mocker.patch("jobless.alerts.requests.get", side_effect=requests.RequestException("boom"))

    alerts.file_or_close_issue(BROKEN)  # must not raise


def test_send_email_summary_does_nothing_without_alert_email(mocker, monkeypatch):
    monkeypatch.delenv("ALERT_EMAIL", raising=False)
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    send_email = mocker.patch("jobless.alerts.digest.send_email")

    alerts.send_email_summary([BROKEN])

    send_email.assert_not_called()


def test_send_email_summary_does_nothing_when_nothing_is_broken(mocker, monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL", "abdullah@example.com")
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    send_email = mocker.patch("jobless.alerts.digest.send_email")

    alerts.send_email_summary([])

    send_email.assert_not_called()


def test_send_email_summary_sends_one_email_listing_every_broken_company(mocker, monkeypatch):
    monkeypatch.setenv("ALERT_EMAIL", "abdullah@example.com")
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    send_email = mocker.patch("jobless.alerts.digest.send_email")

    alerts.send_email_summary([BROKEN])

    send_email.assert_called_once()
    to_email, _subject, html = send_email.call_args[0]
    assert to_email == "abdullah@example.com"
    assert "CompanyA" in html
