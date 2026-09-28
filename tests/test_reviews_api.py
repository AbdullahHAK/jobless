from datetime import datetime

from fastapi.testclient import TestClient

from jobless.api import app, get_db_connection

client = TestClient(app)

VALID_REVIEW = {
    "company": "Arbisoft",
    "role": "Software Engineer",
    "employment_status": "current",
    "rating": 4,
    "salary_range": "150k-200k PKR/month",
    "review_text": "Solid place to work, decent WLB and real mentorship for juniors.",
}


def _override_with(fake_conn):
    def _fake_get_db_connection():
        yield fake_conn

    app.dependency_overrides[get_db_connection] = _fake_get_db_connection


def test_submit_review_adds_pending_review(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    add_review = mocker.patch("jobless.api.db.add_review", return_value=42)

    response = client.post("/reviews", json=VALID_REVIEW)

    assert response.status_code == 201
    assert response.json() == {"status": "pending", "id": 42}
    add_review.assert_called_once_with(
        fake_conn,
        company="Arbisoft",
        employment_status="current",
        rating=4,
        review_text=VALID_REVIEW["review_text"],
        role="Software Engineer",
        salary_range="150k-200k PKR/month",
    )

    app.dependency_overrides.clear()


def test_submit_review_rejects_review_text_too_short():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.post("/reviews", json={**VALID_REVIEW, "review_text": "too short"})

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_submit_review_rejects_invalid_employment_status():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.post("/reviews", json={**VALID_REVIEW, "employment_status": "intern"})

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_submit_review_rejects_rating_out_of_range():
    app.dependency_overrides[get_db_connection] = lambda: iter([object()])

    response = client.post("/reviews", json={**VALID_REVIEW, "rating": 6})

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_submit_review_is_rate_limited_per_client(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.add_review", return_value=1)

    # Limit is 5/hour - fire well past that from the same test client (same
    # source IP) and confirm at least one request gets rejected with 429.
    statuses = [client.post("/reviews", json=VALID_REVIEW).status_code for _ in range(10)]

    assert 429 in statuses

    app.dependency_overrides.clear()


def test_get_reviews_returns_approved_rows_from_db(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch(
        "jobless.api.db.list_reviews",
        return_value=[
            {
                "id": 1,
                "company": "Arbisoft",
                "role": "Software Engineer",
                "employment_status": "current",
                "rating": 4,
                "salary_range": "150k-200k PKR/month",
                "review_text": "Solid place to work.",
                "submitted_at": datetime.now(),
            }
        ],
    )

    response = client.get("/reviews?company=Arbisoft")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["company"] == "Arbisoft"

    app.dependency_overrides.clear()


def test_get_pending_reviews_without_admin_token_is_forbidden(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)

    response = client.get("/reviews/pending")

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_get_pending_reviews_with_correct_admin_token_returns_rows(mocker, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "the-real-token")
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.list_pending_reviews", return_value=[])

    response = client.get("/reviews/pending", headers={"X-Admin-Token": "the-real-token"})

    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_get_pending_reviews_with_wrong_admin_token_is_forbidden(mocker, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "the-real-token")
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)

    response = client.get("/reviews/pending", headers={"X-Admin-Token": "guess"})

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_approve_review_without_admin_token_is_forbidden(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)

    response = client.post("/reviews/1/approve")

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_approve_review_with_admin_token_calls_db(mocker, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "the-real-token")
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    approve_review = mocker.patch("jobless.api.db.approve_review", return_value=True)

    response = client.post("/reviews/7/approve", headers={"X-Admin-Token": "the-real-token"})

    assert response.status_code == 200
    assert response.json() == {"status": "approved"}
    approve_review.assert_called_once_with(fake_conn, 7)

    app.dependency_overrides.clear()


def test_approve_review_returns_404_when_not_found(mocker, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "the-real-token")
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    mocker.patch("jobless.api.db.approve_review", return_value=False)

    response = client.post("/reviews/999/approve", headers={"X-Admin-Token": "the-real-token"})

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_reject_review_with_admin_token_calls_db(mocker, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "the-real-token")
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)
    reject_review = mocker.patch("jobless.api.db.reject_review", return_value=True)

    response = client.post("/reviews/7/reject", headers={"X-Admin-Token": "the-real-token"})

    assert response.status_code == 200
    assert response.json() == {"status": "rejected"}
    reject_review.assert_called_once_with(fake_conn, 7)

    app.dependency_overrides.clear()


def test_reject_review_without_admin_token_is_forbidden(mocker):
    fake_conn = mocker.MagicMock()
    _override_with(fake_conn)

    response = client.post("/reviews/7/reject")

    assert response.status_code == 403

    app.dependency_overrides.clear()
