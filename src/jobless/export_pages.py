import logging
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

from . import db

logger = logging.getLogger(__name__)


# Job title/company/location are scraped third-party text from 42+ different
# career pages, not trusted input - every one of these templates embeds them
# into both HTML text nodes and quoted attributes (href, content="..."), so
# this escapes quotes too rather than relying on xml.sax.saxutils.escape's
# default (which only covers &/</>). Same discipline as app.js's
# escapeHtml() for the exact same reason - see the stored-XSS fix there.
def xml_escape(value: str) -> str:
    return _xml_escape(str(value), {'"': "&quot;", "'": "&#39;"})

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
JOBS_DIR = FRONTEND_DIR / "jobs"
COMPANIES_DIR = FRONTEND_DIR / "companies"
SITEMAP_PATH = FRONTEND_DIR / "sitemap.xml"

SITE_URL = "https://abdullahhak.github.io/jobless"
OG_IMAGE_URL = f"{SITE_URL}/assets/og-image.png"

# Best-effort structured-address mapping for JobPosting schema - location
# strings are free text scraped from dozens of different career pages
# ("Lahore, Punjab, Pakistan", "Islamabad/Rawalpindi", bare "Lahore", etc.),
# so this only recognizes the few major cities worth naming explicitly;
# anything else still gets a valid (if less structured) address.
KNOWN_CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Multan", "Faisalabad"]

STATIC_PAGES = [
    ("", "daily", "1.0"),
    ("prep.html", "weekly", "0.8"),
    ("reviews.html", "daily", "0.7"),
    ("about.html", "monthly", "0.5"),
]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80].strip("-") or "job"


def _guess_city(location: str) -> str:
    for city in KNOWN_CITIES:
        if city.lower() in location.lower():
            return city
    return location


# Every page on this static site repeats the same sidebar/header markup
# (no templating engine, no build step) - this is that shell, parameterized
# just enough to serve job/company pages living one directory level down
# from the handwritten pages, hence the leading "../" on every asset link.
def _page_shell(*, title: str, description: str, canonical_url: str, body: str, active: str = "") -> str:
    nav_class = {name: (" site-nav-active" if name == active else "") for name in ("jobs", "prep", "reviews", "about")}
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{xml_escape(description)}" />
  <title>{xml_escape(title)}</title>
  <link rel="canonical" href="{xml_escape(canonical_url)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{xml_escape(canonical_url)}" />
  <meta property="og:title" content="{xml_escape(title)}" />
  <meta property="og:description" content="{xml_escape(description)}" />
  <meta property="og:image" content="{OG_IMAGE_URL}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{xml_escape(title)}" />
  <meta name="twitter:description" content="{xml_escape(description)}" />
  <meta name="twitter:image" content="{OG_IMAGE_URL}" />
  <meta name="theme-color" content="#09090b" />
  <link rel="icon" type="image/svg+xml" href="../favicon.svg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../style.css" />
</head>
<body>
  <button id="sidebar-toggle" class="sidebar-toggle" aria-label="Toggle navigation">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  </button>
  <div id="sidebar-backdrop" class="sidebar-backdrop"></div>

  <aside class="sidebar">
    <a class="site-logo" href="../index.html">Jobless</a>
    <nav class="sidebar-nav">
      <a href="../index.html" class="{nav_class["jobs"]}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="14" rx="2" />
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        </svg>
        Jobs
      </a>
      <a href="../prep.html" class="{nav_class["prep"]}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="6" />
          <circle cx="12" cy="12" r="2" />
        </svg>
        Prep
      </a>
      <a href="../reviews.html" class="{nav_class["reviews"]}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
        Reviews
      </a>
      <a href="../about.html" class="{nav_class["about"]}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4M12 8h.01" />
        </svg>
        About
      </a>
    </nav>
    <div class="sidebar-footer">
      <p>Built by <a href="https://github.com/AbdullahHAK" target="_blank" rel="noopener">Abdullah</a></p>
      <p><a href="https://github.com/AbdullahHAK/jobless" target="_blank" rel="noopener">Source on GitHub ↗</a></p>
      <p><a href="https://github.com/AbdullahHAK/jobless/issues/new?template=company-suggestion.yml" target="_blank" rel="noopener">Suggest a company ↗</a></p>
      <p>Free for everyone, updated daily</p>
    </div>
  </aside>

  <div class="page-content">
{body}
  </div>

  <script src="../sidebar.js"></script>
</body>
</html>
"""


def _job_posting_schema(job: dict, canonical_url: str) -> str:
    city = _guess_city(job["location"])
    description = (
        f"Jobless lists this {job['title']} opening at {job['company']}, located in "
        f"{job['location']}. This listing is aggregated directly from {job['company']}'s own "
        "careers page - click Apply to view the full description and apply on their site."
    )
    return f"""{{
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "title": {_json_str(job["title"])},
    "description": {_json_str(description)},
    "datePosted": "{job["first_seen_at"].date().isoformat()}",
    "hiringOrganization": {{
      "@type": "Organization",
      "name": {_json_str(job["company"])}
    }},
    "jobLocation": {{
      "@type": "Place",
      "address": {{
        "@type": "PostalAddress",
        "addressLocality": {_json_str(city)},
        "addressCountry": "PK"
      }}
    }},
    "url": "{canonical_url}"
  }}"""


def _json_str(value: str) -> str:
    # Minimal JSON string escaping for embedding inside the hand-built
    # JSON-LD block above - avoids pulling in json.dumps for one field at a
    # time while still handling quotes/backslashes/newlines correctly.
    # Critically, "<" is escaped as the JSON-valid \u003c rather than left
    # literal: this JSON gets embedded inside an actual <script> tag, so an
    # unescaped "</script>" in a scraped job title would otherwise close
    # the tag early and inject arbitrary HTML/JS - same stored-XSS class
    # already fixed once in app.js for the same untrusted scraped-title data.
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("<", "\\u003c")
    return '"' + escaped + '"'


def _job_page_html(job: dict, slug: str) -> str:
    canonical_url = f"{SITE_URL}/jobs/{job['id']}-{slug}.html"
    title = f"{job['title']} at {job['company']} — Jobless"
    description = f"{job['title']} at {job['company']} in {job['location']}. Listed on Jobless, updated daily."
    company_slug = slugify(job["company"])

    body = f"""    <header class="page-hero job-detail-hero">
      <p class="job-detail-breadcrumb">
        <a href="../index.html">All jobs</a> ·
        <a href="../companies/{xml_escape(company_slug)}.html">{xml_escape(job["company"])} jobs</a>
      </p>
      <h1>{xml_escape(job["title"])}</h1>
      <p class="tagline">{xml_escape(job["company"])} · {xml_escape(job["location"])}</p>
    </header>

    <main class="prep-main">
      <section class="prep-section job-detail-section">
        <p class="prep-section-intro">
          This {xml_escape(job["title"])} opening at {xml_escape(job["company"])} was first seen on
          Jobless on {job["first_seen_at"].date().isoformat()} and last confirmed open on
          {job["date_scraped"].isoformat()}. It's aggregated directly from {xml_escape(job["company"])}'s
          own careers page, not re-typed or summarized - the full description, requirements, and
          application form live on their site.
        </p>
        <a class="hero-cta job-detail-apply" href="{xml_escape(str(job["apply_link"]))}" target="_blank" rel="noopener">
          <span>Apply on {xml_escape(job["company"])}'s site</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </a>
      </section>
    </main>

    <script type="application/ld+json">
{_job_posting_schema(job, canonical_url)}
    </script>"""

    return _page_shell(title=title, description=description, canonical_url=canonical_url, body=body)


def _company_page_html(company: str, jobs: list[dict], logo_by_company: dict[str, str]) -> str:
    slug = slugify(company)
    canonical_url = f"{SITE_URL}/companies/{slug}.html"
    title = f"{company} Jobs — Jobless"
    description = f"{len(jobs)} open role{'s' if len(jobs) != 1 else ''} at {company}, aggregated daily from their own careers page."

    logo_file = logo_by_company.get(company)
    logo_html = (
        f'<img class="company-detail-logo" src="../assets/logos/{xml_escape(logo_file)}" alt="{xml_escape(company)}" />'
        if logo_file
        else ""
    )

    rows = "\n".join(
        f"""        <li class="prep-card">
          <a class="job-title" href="../jobs/{job["id"]}-{slugify(job["title"] + "-" + company)}.html">{xml_escape(job["title"])}</a>
          <div class="job-meta">{xml_escape(job["location"])} · seen {job["date_scraped"].isoformat()}</div>
        </li>"""
        for job in jobs
    )

    body = f"""    <header class="page-hero">
      {logo_html}
      <h1>{xml_escape(company)} Jobs</h1>
      <p class="tagline">{len(jobs)} open role{"s" if len(jobs) != 1 else ""} tracked right now, aggregated daily from {xml_escape(company)}'s own careers page.</p>
    </header>

    <main class="prep-main">
      <section class="prep-section">
        <ul class="job-list">
{rows}
        </ul>
      </section>
    </main>"""

    return _page_shell(title=title, description=description, canonical_url=canonical_url, body=body)


def _load_logo_map() -> dict[str, str]:
    import json

    logos_path = FRONTEND_DIR / "data" / "company-logos.json"
    try:
        entries = json.loads(logos_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {entry["company"]: entry["logo"] for entry in entries if entry.get("logo")}


def _write_sitemap(company_slugs: list[str], job_entries: list[tuple[int, str]]) -> None:
    urls = [f"{SITE_URL}/{path}" for path, _freq, _priority in STATIC_PAGES]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, changefreq, priority in STATIC_PAGES:
        lines.append(
            f"  <url><loc>{SITE_URL}/{path}</loc><changefreq>{changefreq}</changefreq>"
            f"<priority>{priority}</priority></url>"
        )
    for slug in company_slugs:
        lines.append(
            f"  <url><loc>{SITE_URL}/companies/{slug}.html</loc><changefreq>daily</changefreq>"
            "<priority>0.6</priority></url>"
        )
    for job_id, slug in job_entries:
        lines.append(
            f"  <url><loc>{SITE_URL}/jobs/{job_id}-{slug}.html</loc><changefreq>weekly</changefreq>"
            "<priority>0.5</priority></url>"
        )
    lines.append("</urlset>")
    SITEMAP_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote sitemap with %d urls", len(urls) + len(company_slugs) + len(job_entries))


def export(jobs: list[dict]) -> tuple[int, int]:
    """Regenerates every job/company detail page and the sitemap from
    scratch each run, rather than diffing against what's already there -
    closed jobs and companies with zero current postings simply stop being
    regenerated, so their pages naturally 404 instead of lingering forever
    as stale, never-pruned listings."""
    shutil.rmtree(JOBS_DIR, ignore_errors=True)
    shutil.rmtree(COMPANIES_DIR, ignore_errors=True)
    JOBS_DIR.mkdir(parents=True)
    COMPANIES_DIR.mkdir(parents=True)

    logo_by_company = _load_logo_map()

    jobs_by_company: dict[str, list[dict]] = {}
    job_entries: list[tuple[int, str]] = []
    for job in jobs:
        jobs_by_company.setdefault(job["company"], []).append(job)
        slug = slugify(f"{job['title']}-{job['company']}")
        (JOBS_DIR / f"{job['id']}-{slug}.html").write_text(_job_page_html(job, slug), encoding="utf-8")
        job_entries.append((job["id"], slug))

    company_slugs = []
    for company, company_jobs in jobs_by_company.items():
        slug = slugify(company)
        company_slugs.append(slug)
        (COMPANIES_DIR / f"{slug}.html").write_text(
            _company_page_html(company, company_jobs, logo_by_company), encoding="utf-8"
        )

    _write_sitemap(sorted(company_slugs), job_entries)

    logger.info("generated %d job pages and %d company pages", len(job_entries), len(company_slugs))
    return len(job_entries), len(company_slugs)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    conn = db.get_connection()
    try:
        jobs = db.list_all_jobs(conn)
    finally:
        conn.close()
    export(jobs)


if __name__ == "__main__":
    main()
