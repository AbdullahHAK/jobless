from datetime import date, datetime

from fastapi.testclient import TestClient

from jobless import db
from jobless.api import app, get_db_connection

client = TestClient(app)


def _override_with(fake_conn):
    def _fake_get_db_connection():
        yield fake_conn

    app.dependency_overrides[get_db_connection] = _fake_get_db_connection


def test_health_returns_ok(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    fake_conn.execute.assert_called_once_with("SELECT 1")

    app.dependency_overrides.clear()


def test_get_jobs_returns_rows_from_db(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch(
        "jobless.api.db.list_jobs",
        return_value=[
            {
                "id": 1,
                "title": "Senior Software Engineer",
                "company": "Arbisoft",
                "location": "Lahore",
                "apply_link": "https://example.com/jobs/1",
                "date_scraped": date.today(),
                "first_seen_at": datetime.now(),
            }
        ],
    )

    response = client.get("/jobs?company=Arbisoft&limit=10")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Senior Software Engineer"
    assert body[0]["company"] == "Arbisoft"

    app.dependency_overrides.clear()


def test_get_jobs_rejects_limit_over_max():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.get("/jobs?limit=500")

    assert response.status_code == 422

    app.dependency_overrides.clear()
