# Jobless

A daily-updated job board for the Pakistani software industry. Scrapes career pages of
software houses and aggregates every opening into one place, so job seekers can browse and
apply directly instead of checking 15+ company sites individually.

## How it works

Each company is a self-contained scraper module implementing a common interface that
returns a standard `Job` (title, company, location, apply_link, date_scraped). A registry
auto-discovers every scraper dropped into `src/jobless/scrapers/` - no wiring required to
add a new one. Each scraper has isolated error handling, so one company's site changing
doesn't take down the rest of the run. Results are upserted into PostgreSQL keyed on
`apply_link`, so re-scraping a still-open job updates it in place instead of duplicating it.

Currently scraping 15 companies: Arbisoft, Devsinc, Folio3, Confiz, Codup, Tkxel, 10Pearls,
Contour Software, VentureDive, NetSol Technologies, Abacus Consulting, Kualitatem, EurosHub,
InvoZone, and Nextbridge. Each scraper picks whatever data source is actually cleanest for
that site - static HTML, a public JSON API discovered via network inspection, or (rarely) a
JS payload embedded in the page - documented in a comment at the top of each scraper module.

## Stack

- **Scraping**: Python, `requests` + BeautifulSoup (Playwright available for one-off
  reconnaissance of JS-heavy sites, not needed at runtime by any current scraper)
- **Storage**: PostgreSQL
- **Backend**: FastAPI (`GET /jobs`, `GET /companies`, `GET /health`, `GET /metrics`)
- **Frontend**: plain HTML/CSS/JS, no framework or build step
- **Containers**: Docker (multi-stage builds) for the API, scraper, and frontend
- **Orchestration**: Kubernetes via a Helm chart (`charts/jobless/`); the scraper runs as a
  CronJob, the API/frontend as Deployments
- **CI**: GitHub Actions - tests + Docker builds on every push, security scanning (Trivy +
  pip-audit) on every push, a manually-triggered full smoke test (KinD + Helm + live scrape)
- **GitOps**: an ArgoCD `Application` manifest (`argocd/`) for syncing the cluster to `main`
- **Monitoring**: `/metrics` in Prometheus format, plus a `ServiceMonitor` for
  kube-prometheus-stack to pick it up automatically

## Running it locally

```bash
uv sync                              # install dependencies
docker compose up -d                 # start Postgres
uv run jobless                       # run every scraper once, store results
uv run uvicorn jobless.api:app --reload   # serve the API on :8000
```

Then open `frontend/index.html` (e.g. `python -m http.server` from `frontend/`) with the API
running - it fetches from `http://localhost:8000` by default.

```bash
uv run python -m pytest -v           # run the test suite
```

## Deploying

```bash
docker build -t jobless-api -f Dockerfile .
docker build -t jobless-scraper -f Dockerfile.scraper .
docker build -t jobless-frontend -f Dockerfile.frontend .

helm install jobless charts/jobless --create-namespace --namespace jobless
```

`scripts/smoke-test.sh` runs the full build → KinD cluster → Helm install → trigger a scrape
→ verify the API sequence end to end; it's also wired up as a manually-triggered GitHub
Actions workflow (`smoke-test.yml`) since it does a real scrape of all 15 companies' live
sites and shouldn't run automatically on every push.
