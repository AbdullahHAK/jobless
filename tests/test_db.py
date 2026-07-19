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
