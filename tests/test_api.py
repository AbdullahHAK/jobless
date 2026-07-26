from datetime import date, datetime

from fastapi.testclient import TestClient

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


def test_get_companies_returns_distinct_list(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.list_companies", return_value=["Arbisoft", "Confiz"])

    response = client.get("/companies")

    assert response.status_code == 200
    assert response.json() == ["Arbisoft", "Confiz"]

    app.dependency_overrides.clear()


def test_get_jobs_rejects_limit_over_max():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.get("/jobs?limit=500")

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_subscribe_adds_subscriber(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    add_subscriber = mocker.patch("jobless.api.db.add_subscriber", return_value="a-token")

    response = client.post(
        "/subscribe",
        json={"name": "Abdullah", "email": "abdullah@example.com", "frequency": "daily"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "subscribed"}
    add_subscriber.assert_called_once_with(
        fake_conn, name="Abdullah", email="abdullah@example.com", frequency="daily"
    )

    app.dependency_overrides.clear()


def test_subscribe_rejects_invalid_email():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.post(
        "/subscribe",
        json={"name": "Abdullah", "email": "not-an-email", "frequency": "daily"},
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_subscribe_rejects_invalid_frequency():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.post(
        "/subscribe",
        json={"name": "Abdullah", "email": "abdullah@example.com", "frequency": "monthly"},
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_unsubscribe_removes_subscriber_and_returns_html(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.remove_subscriber", return_value=True)

    response = client.get("/unsubscribe?token=some-token")

    assert response.status_code == 200
    assert "unsubscribed" in response.text.lower()

    app.dependency_overrides.clear()


def test_unsubscribe_with_unknown_token_returns_404(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.remove_subscriber", return_value=False)

    response = client.get("/unsubscribe?token=unknown-token")

    assert response.status_code == 404

    app.dependency_overrides.clear()
