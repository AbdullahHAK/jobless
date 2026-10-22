import json
from datetime import date, datetime

import pytest

from jobless import export_pages

JOB_A = {
    "id": 1,
    "title": "Senior Software Engineer",
    "company": "Arbisoft",
    "location": "Lahore, Pakistan",
    "apply_link": "https://example.com/jobs/1",
    "date_scraped": date(2026, 10, 20),
    "first_seen_at": datetime(2026, 10, 1, 12, 0, 0),
}
JOB_B = {
    "id": 2,
    "title": "QA Engineer",
    "company": "Arbisoft",
    "location": "Karachi",
    "apply_link": "https://example.com/jobs/2",
    "date_scraped": date(2026, 10, 20),
    "first_seen_at": datetime(2026, 10, 15, 9, 0, 0),
}


@pytest.fixture(autouse=True)
def _redirect_output_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(export_pages, "FRONTEND_DIR", tmp_path)
    monkeypatch.setattr(export_pages, "JOBS_DIR", tmp_path / "jobs")
    monkeypatch.setattr(export_pages, "COMPANIES_DIR", tmp_path / "companies")
    monkeypatch.setattr(export_pages, "SITEMAP_PATH", tmp_path / "sitemap.xml")
    return tmp_path


def test_slugify_handles_punctuation_and_length():
    assert export_pages.slugify("Senior Software Engineer!! (Remote)") == "senior-software-engineer-remote"
    assert export_pages.slugify("") == "job"
    assert len(export_pages.slugify("x" * 500)) <= 80


def test_export_writes_one_page_per_job_and_per_company(_redirect_output_dirs):
    job_count, company_count = export_pages.export([JOB_A, JOB_B])

    assert job_count == 2
    assert company_count == 1
    job_files = list(export_pages.JOBS_DIR.glob("*.html"))
    assert len(job_files) == 2
    company_files = list(export_pages.COMPANIES_DIR.glob("*.html"))
    assert len(company_files) == 1
    assert (export_pages.COMPANIES_DIR / "arbisoft.html").exists()


def test_job_page_contains_jobposting_schema_and_apply_link(_redirect_output_dirs):
    export_pages.export([JOB_A])

    html = next(export_pages.JOBS_DIR.glob("1-*.html")).read_text(encoding="utf-8")
    assert '"@type": "JobPosting"' in html
    assert '"title": "Senior Software Engineer"' in html
    assert '"datePosted": "2026-10-01"' in html
    assert "https://example.com/jobs/1" in html
    assert "Arbisoft" in html


def test_company_page_lists_its_jobs(_redirect_output_dirs):
    export_pages.export([JOB_A, JOB_B])

    html = (export_pages.COMPANIES_DIR / "arbisoft.html").read_text(encoding="utf-8")
    assert "Senior Software Engineer" in html
    assert "QA Engineer" in html
    assert "2 open roles" in html


def test_sitemap_includes_static_job_and_company_urls(_redirect_output_dirs):
    export_pages.export([JOB_A])

    xml = export_pages.SITEMAP_PATH.read_text(encoding="utf-8")
    assert "https://abdullahhak.github.io/jobless/" in xml
    assert "https://abdullahhak.github.io/jobless/companies/arbisoft.html" in xml
    assert "https://abdullahhak.github.io/jobless/jobs/1-" in xml


def test_export_removes_stale_pages_from_a_previous_run(_redirect_output_dirs):
    export_pages.export([JOB_A, JOB_B])
    assert len(list(export_pages.JOBS_DIR.glob("*.html"))) == 2

    # Second run with only one of the two jobs still active - the stale
    # job's page shouldn't survive the regenerate.
    export_pages.export([JOB_A])

    remaining = list(export_pages.JOBS_DIR.glob("*.html"))
    assert len(remaining) == 1
    assert "1-" in remaining[0].name


def test_html_escapes_job_title_with_special_characters(_redirect_output_dirs):
    malicious_job = {**JOB_A, "title": '<script>alert("x")</script>'}
    export_pages.export([malicious_job])

    html = next(export_pages.JOBS_DIR.glob("1-*.html")).read_text(encoding="utf-8")
    assert "<script>alert" not in html


def test_jsonld_script_cannot_be_broken_out_of_by_a_malicious_title(_redirect_output_dirs):
    malicious_job = {**JOB_A, "title": "Engineer</script><script>alert(1)</script>"}
    export_pages.export([malicious_job])

    html = next(export_pages.JOBS_DIR.glob("1-*.html")).read_text(encoding="utf-8")
    start = html.index('<script type="application/ld+json">') + len('<script type="application/ld+json">')
    end = html.index("</script>", start)
    raw_json = html[start:end]

    # The real guarantee: this extracted block still parses as the intended
    # JobPosting object. If the malicious title had broken out early, this
    # would either fail to parse or yield a truncated/wrong fragment.
    parsed = json.loads(raw_json)
    assert parsed["@type"] == "JobPosting"
    assert "alert(1)" in parsed["title"]
    # And the injected tag never appears as live, executable markup anywhere
    # in the page - only as inert data inside the JSON string.
    assert "<script>alert(1)</script>" not in html


def test_company_page_includes_logo_when_mapping_exists(_redirect_output_dirs, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "company-logos.json").write_text(
        json.dumps([{"company": "Arbisoft", "logo": "arbisoft.svg"}]), encoding="utf-8"
    )

    export_pages.export([JOB_A])

    html = (export_pages.COMPANIES_DIR / "arbisoft.html").read_text(encoding="utf-8")
    assert "assets/logos/arbisoft.svg" in html
