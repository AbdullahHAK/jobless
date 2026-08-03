import json
from datetime import date, datetime

from jobless import export_static

JOB_ROW = {
    "id": 1,
    "title": "Senior Software Engineer",
    "company": "Arbisoft",
    "location": "Lahore",
    "apply_link": "https://example.com/jobs/1",
    "date_scraped": date(2026, 7, 31),
    "first_seen_at": datetime(2026, 7, 31, 12, 0, 0),
}


def test_export_writes_json_file_with_serialized_dates(mocker, tmp_path):
    mocker.patch("jobless.export_static.db.get_connection")
    mocker.patch("jobless.export_static.db.list_all_jobs", return_value=[JOB_ROW])
    output_path = tmp_path / "data" / "jobs.json"

    count = export_static.export(output_path)

    assert count == 1
    assert output_path.exists()

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written[0]["title"] == "Senior Software Engineer"
    assert written[0]["date_scraped"] == "2026-07-31"
    assert written[0]["first_seen_at"] == "2026-07-31T12:00:00"


def test_export_creates_parent_directory_if_missing(mocker, tmp_path):
    mocker.patch("jobless.export_static.db.get_connection")
    mocker.patch("jobless.export_static.db.list_all_jobs", return_value=[])
    output_path = tmp_path / "nested" / "dir" / "jobs.json"

    export_static.export(output_path)

    assert output_path.exists()
