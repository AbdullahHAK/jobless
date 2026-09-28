from datetime import date

from jobless import db
from jobless.scrapers.base import Job

JOB = Job(
    title="Senior Software Engineer",
    company="Arbisoft",
    location="Lahore",
    apply_link="https://example.com/jobs/1",
    date_scraped=date.today(),
)


def test_init_db_executes_schema_and_commits(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    db.init_db(conn)

    cursor.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS jobs" in cursor.execute.call_args[0][0]
    conn.commit.assert_called_once()


def test_save_jobs_upserts_by_apply_link_and_commits(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    count = db.save_jobs(conn, [JOB])

    assert count == 1
    cursor.executemany.assert_called_once()
    sql, rows = cursor.executemany.call_args[0]
    assert "ON CONFLICT (apply_link) DO UPDATE" in sql
    assert rows == [
        {
            "title": "Senior Software Engineer",
            "company": "Arbisoft",
            "location": "Lahore",
            "apply_link": "https://example.com/jobs/1",
            "date_scraped": JOB.date_scraped,
        }
    ]
    conn.commit.assert_called_once()


def test_save_jobs_with_empty_list_skips_db_calls(mocker):
    conn = mocker.MagicMock()

    count = db.save_jobs(conn, [])

    assert count == 0
    conn.cursor.assert_not_called()
    conn.commit.assert_not_called()


def test_list_companies_returns_distinct_sorted_names(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [("Arbisoft",), ("Confiz",)]

    companies = db.list_companies(conn)

    assert companies == ["Arbisoft", "Confiz"]
    assert "DISTINCT company" in cursor.execute.call_args[0][0]


def test_list_new_jobs_filters_by_first_seen_at(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [{"id": 1, "title": "Senior Engineer"}]
    since = date.today()

    jobs = db.list_new_jobs(conn, since)

    assert jobs == [{"id": 1, "title": "Senior Engineer"}]
    sql, params = cursor.execute.call_args[0]
    assert "first_seen_at >=" in sql
    assert params == {"since": since}


def test_list_all_jobs_returns_everything_unpaginated(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]

    jobs = db.list_all_jobs(conn)

    assert jobs == [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
    sql = cursor.execute.call_args[0][0]
    assert "LIMIT" not in sql
    assert "OFFSET" not in sql


def test_add_subscriber_upserts_by_email_and_returns_token(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("the-existing-token",)

    token = db.add_subscriber(conn, name="Abdullah", email="a@example.com", frequency="daily")

    assert token == "the-existing-token"
    sql, params = cursor.execute.call_args[0]
    assert "ON CONFLICT (email) DO UPDATE" in sql
    assert "unsubscribe_token" not in sql.split("DO UPDATE SET")[1].split("RETURNING")[0]
    assert params["name"] == "Abdullah"
    assert params["email"] == "a@example.com"
    assert params["frequency"] == "daily"
    conn.commit.assert_called_once()


def test_remove_subscriber_returns_true_when_a_row_was_deleted(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1

    assert db.remove_subscriber(conn, "some-token") is True
    conn.commit.assert_called_once()


def test_remove_subscriber_returns_false_when_token_not_found(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 0

    assert db.remove_subscriber(conn, "unknown-token") is False


def test_list_subscribers_filters_by_frequency(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [{"id": 1, "name": "Abdullah", "email": "a@example.com", "unsubscribe_token": "t"}]

    subscribers = db.list_subscribers(conn, "daily")

    assert len(subscribers) == 1
    assert cursor.execute.call_args[0][1] == {"frequency": "daily"}


def test_close_stale_jobs_marks_missing_jobs_inactive_and_commits(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 2

    closed = db.close_stale_jobs(conn, "Arbisoft", ["https://example.com/jobs/1"])

    assert closed == 2
    sql, params = cursor.execute.call_args[0]
    assert "SET is_active = false" in sql
    assert "apply_link != ALL(%(active_links)s)" in sql
    assert params == {"company": "Arbisoft", "active_links": ["https://example.com/jobs/1"]}
    conn.commit.assert_called_once()


def test_close_stale_jobs_with_no_active_links_closes_everything_for_that_company(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 3

    closed = db.close_stale_jobs(conn, "NetSol Technologies", [])

    assert closed == 3
    params = cursor.execute.call_args[0][1]
    assert params["active_links"] == []


def test_list_jobs_only_returns_active_jobs(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_jobs(conn)

    sql = cursor.execute.call_args[0][0]
    assert "is_active = true" in sql


def test_list_all_jobs_only_returns_active_jobs(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_all_jobs(conn)

    sql = cursor.execute.call_args[0][0]
    assert "is_active = true" in sql


def test_list_companies_only_counts_active_jobs(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_companies(conn)

    sql = cursor.execute.call_args[0][0]
    assert "is_active = true" in sql


def test_add_review_inserts_unapproved_and_returns_id(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (7,)

    review_id = db.add_review(
        conn,
        company="Arbisoft",
        employment_status="current",
        rating=4,
        review_text="Solid place to work, decent WLB and mentorship for juniors.",
        role="Software Engineer",
        salary_range="150k-200k PKR/month",
    )

    assert review_id == 7
    sql, params = cursor.execute.call_args[0]
    assert "is_approved" not in sql.split("VALUES")[0]  # column list omits it - defaults to false
    assert params["company"] == "Arbisoft"
    assert params["rating"] == 4
    conn.commit.assert_called_once()


def test_list_reviews_only_returns_approved_reviews(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_reviews(conn)

    sql = cursor.execute.call_args[0][0]
    assert "is_approved = true" in sql


def test_list_reviews_filters_by_company_when_given(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_reviews(conn, company="Arbisoft")

    sql, params = cursor.execute.call_args[0]
    assert "AND company = %(company)s" in sql
    assert params == {"company": "Arbisoft"}


def test_list_pending_reviews_only_returns_unapproved(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    db.list_pending_reviews(conn)

    sql = cursor.execute.call_args[0][0]
    assert "is_approved = false" in sql


def test_approve_review_returns_true_when_a_pending_row_was_updated(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1

    assert db.approve_review(conn, 7) is True
    conn.commit.assert_called_once()


def test_approve_review_returns_false_when_not_found(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 0

    assert db.approve_review(conn, 999) is False


def test_reject_review_deletes_only_unapproved_rows(mocker):
    conn = mocker.MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1

    assert db.reject_review(conn, 7) is True
    sql = cursor.execute.call_args[0][0]
    assert "DELETE FROM reviews" in sql
    assert "is_approved = false" in sql
    conn.commit.assert_called_once()
