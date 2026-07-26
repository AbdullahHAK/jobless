from datetime import datetime

import requests

from jobless import digest

JOB = {
    "id": 1,
    "title": "Senior Software Engineer",
    "company": "Arbisoft",
    "location": "Lahore",
    "apply_link": "https://example.com/jobs/1",
    "first_seen_at": datetime.now(),
}

SUBSCRIBER = {"id": 1, "name": "Abdullah", "email": "a@example.com", "unsubscribe_token": "tok123"}


def test_render_email_html_includes_job_and_unsubscribe_link():
    html = digest.render_email_html([JOB], "https://example.com/unsubscribe?token=tok123")

    assert "Senior Software Engineer" in html
    assert "Arbisoft" in html
    assert "https://example.com/jobs/1" in html
    assert "https://example.com/unsubscribe?token=tok123" in html


def test_send_email_posts_to_resend_with_auth_header(mocker, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    mock_post = mocker.patch("jobless.digest.requests.post")
    mock_post.return_value = mocker.Mock(raise_for_status=lambda: None)

    digest.send_email("a@example.com", "Subject", "<p>hi</p>")

    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["to"] == ["a@example.com"]
    assert kwargs["json"]["from"] == digest.DEFAULT_FROM_EMAIL


def test_run_skips_sending_when_no_new_jobs(mocker):
    mocker.patch("jobless.digest.db.get_connection")
    mocker.patch("jobless.digest.db.list_new_jobs", return_value=[])
    list_subscribers = mocker.patch("jobless.digest.db.list_subscribers")
    send_email = mocker.patch("jobless.digest.send_email")

    digest.run("daily")

    list_subscribers.assert_not_called()
    send_email.assert_not_called()


def test_run_sends_to_each_subscriber_and_continues_after_one_failure(mocker, monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://example.com")
    mocker.patch("jobless.digest.db.get_connection")
    mocker.patch("jobless.digest.db.list_new_jobs", return_value=[JOB])
    mocker.patch(
        "jobless.digest.db.list_subscribers",
        return_value=[SUBSCRIBER, {**SUBSCRIBER, "id": 2, "email": "b@example.com", "unsubscribe_token": "tok456"}],
    )
    send_email = mocker.patch("jobless.digest.send_email", side_effect=[requests.RequestException("boom"), None])

    digest.run("daily")

    assert send_email.call_count == 2
    second_call_args = send_email.call_args_list[1][0]
    assert second_call_args[0] == "b@example.com"
