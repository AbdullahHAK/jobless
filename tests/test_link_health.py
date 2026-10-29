from datetime import date

import requests

from jobless import link_health
from jobless.scrapers.base import Job


def _job(apply_link: str) -> Job:
    return Job(
        title="Software Engineer",
        company="CompanyA",
        location="Lahore",
        apply_link=apply_link,
        date_scraped=date.today(),
    )


def test_filter_live_jobs_drops_404_and_410(mocker):
    live_job = _job("https://example.com/live")
    dead_job = _job("https://example.com/gone-404")
    also_dead_job = _job("https://example.com/gone-410")

    def fake_get(url, **kwargs):
        status = {
            "https://example.com/live": 200,
            "https://example.com/gone-404": 404,
            "https://example.com/gone-410": 410,
        }[url]
        response = mocker.MagicMock()
        response.status_code = status
        response.__enter__ = lambda self: response
        response.__exit__ = lambda self, *a: None
        return response

    mocker.patch("jobless.link_health.requests.get", side_effect=fake_get)

    result = link_health.filter_live_jobs([live_job, dead_job, also_dead_job])

    assert result == [live_job]


def test_filter_live_jobs_keeps_job_on_network_error(mocker):
    job = _job("https://example.com/flaky")
    mocker.patch("jobless.link_health.requests.get", side_effect=requests.ConnectionError("boom"))

    result = link_health.filter_live_jobs([job])

    assert result == [job]


def test_filter_live_jobs_keeps_job_on_403_or_5xx(mocker):
    forbidden_job = _job("https://example.com/forbidden")
    server_error_job = _job("https://example.com/server-error")

    def fake_get(url, **kwargs):
        status = {
            "https://example.com/forbidden": 403,
            "https://example.com/server-error": 503,
        }[url]
        response = mocker.MagicMock()
        response.status_code = status
        response.__enter__ = lambda self: response
        response.__exit__ = lambda self, *a: None
        return response

    mocker.patch("jobless.link_health.requests.get", side_effect=fake_get)

    result = link_health.filter_live_jobs([forbidden_job, server_error_job])

    assert result == [forbidden_job, server_error_job]


def test_filter_live_jobs_returns_empty_list_unchanged():
    assert link_health.filter_live_jobs([]) == []
