// Job listings are a static file regenerated daily by GitHub Actions and
// committed back into the repo - no backend needed to browse jobs at all.
const JOBS_DATA_URL = "data/jobs.json";
// Unlike jobs.json, this is hand-curated (not touched by the daily scrape) -
// the employers here run generic or bot-blocked HR portals we can't scrape,
// but the program info itself is stable enough to maintain by hand.
const PROGRAMS_DATA_URL = "data/programs.json";
const PAGE_SIZE = 50;

// Matches job titles aimed at recent grads - the audience this portal is
// increasingly focused on, alongside general listings.
const ENTRY_LEVEL_PATTERN = /\b(intern(ship)?|graduate|entry[- ]level|fresh(er)?|trainee)\b/i;

// Applied-jobs tracking is entirely client-side (no accounts, no backend) -
// stored in localStorage so it survives reloads but stays private to this
// browser. Wrapped in try/catch since localStorage can throw in some
// contexts (private browsing, storage disabled) - the toggle should still
// work for the current page view even if it can't persist.
const APPLIED_STORAGE_KEY = "jobless:applied";

function loadAppliedLinks() {
  try {
    const raw = localStorage.getItem(APPLIED_STORAGE_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

function saveAppliedLinks(links) {
  try {
    localStorage.setItem(APPLIED_STORAGE_KEY, JSON.stringify([...links]));
  } catch {
    // Couldn't persist (private mode, storage full, etc.) - the toggle
    // still works for this page view, it just won't survive a reload.
  }
}

const state = {
  allJobs: [],
  filtered: [],
  shown: 0,
  company: "",
  entryLevelOnly: false,
  hideApplied: false,
  appliedLinks: loadAppliedLinks(),
};

const jobList = document.getElementById("job-list");
const statusEl = document.getElementById("status");
const resultCount = document.getElementById("result-count");
const loadMoreBtn = document.getElementById("load-more");
const companyFilter = document.getElementById("company-filter");
const entryLevelFilter = document.getElementById("entry-level-filter");
const hideAppliedFilter = document.getElementById("hide-applied-filter");

// Job titles/locations come from scraped third-party career pages, not
// data we control - escape before injecting into innerHTML so a stray
// "<"/">"/quote in a company's own posting can't run as markup/script.
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function programCardHtml(program) {
  return `
    <li class="program-card">
      <a class="program-title" href="${escapeHtml(program.link)}" target="_blank" rel="noopener">${escapeHtml(program.company)} - ${escapeHtml(program.program)}</a>
      <div class="program-meta">${escapeHtml(program.category)} · ${escapeHtml(program.window)}</div>
    </li>
  `;
}

let programsLoaded = false;

async function loadPrograms() {
  if (programsLoaded) return;
  programsLoaded = true;

  const programsList = document.getElementById("programs-list");
  if (!programsList) return;

  programsList.innerHTML = `<li class="status">Loading...</li>`;
  try {
    const response = await fetch(PROGRAMS_DATA_URL);
    if (!response.ok) throw new Error(`${response.status}`);
    const programs = await response.json();
    programsList.innerHTML = programs.map(programCardHtml).join("");
  } catch (err) {
    programsLoaded = false;
    programsList.innerHTML = `<li class="status">Couldn't load programs (${escapeHtml(err.message)}).</li>`;
  }
}

function populateCompanyOptions() {
  const companies = [...new Set(state.allJobs.map((j) => j.company))].sort();
  companyFilter.innerHTML =
    `<option value="">All companies</option>` +
    companies.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
}

const NEW_BADGE_WINDOW_MS = 2 * 24 * 60 * 60 * 1000; // 2 days

function jobCardHtml(job) {
  const date = new Date(job.date_scraped).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const isNew = Date.now() - new Date(job.first_seen_at).getTime() < NEW_BADGE_WINDOW_MS;
  const newBadge = isNew ? `<span class="new-badge">New</span>` : "";
  const link = String(job.apply_link);
  const isApplied = state.appliedLinks.has(link);
  return `
    <li class="job-card${isApplied ? " applied" : ""}">
      <div class="job-card-top">
        <span>
          <a class="job-title" href="${escapeHtml(link)}" target="_blank" rel="noopener">${escapeHtml(job.title)}</a>${newBadge}
        </span>
        <button type="button" class="mark-applied-btn" data-link="${escapeHtml(link)}">${
          isApplied ? "✓ Applied" : "Mark as applied"
        }</button>
      </div>
      <div class="job-meta">${escapeHtml(job.company)} · ${escapeHtml(job.location)} · seen ${date}</div>
    </li>
  `;
}

function renderPage({ reset = false } = {}) {
  if (reset) {
    state.shown = 0;
    jobList.innerHTML = "";
  }

  const nextBatch = state.filtered.slice(state.shown, state.shown + PAGE_SIZE);
  jobList.insertAdjacentHTML("beforeend", nextBatch.map(jobCardHtml).join(""));
  state.shown += nextBatch.length;

  resultCount.textContent = `${state.shown} of ${state.filtered.length} job${state.filtered.length === 1 ? "" : "s"} shown`;
  statusEl.textContent = state.filtered.length === 0 ? "No jobs found." : "";
  loadMoreBtn.hidden = state.shown >= state.filtered.length;
}

function applyFilter() {
  let jobs = state.company ? state.allJobs.filter((j) => j.company === state.company) : state.allJobs;
  if (state.entryLevelOnly) {
    jobs = jobs.filter((j) => ENTRY_LEVEL_PATTERN.test(j.title));
  }
  if (state.hideApplied) {
    jobs = jobs.filter((j) => !state.appliedLinks.has(String(j.apply_link)));
  }
  state.filtered = jobs;
  renderPage({ reset: true });
}

async function loadJobs() {
  statusEl.textContent = "Loading...";
  try {
    const response = await fetch(JOBS_DATA_URL);
    if (!response.ok) throw new Error(`${response.status}`);
    state.allJobs = await response.json();

    populateCompanyOptions();
    applyFilter();
  } catch (err) {
    statusEl.textContent = `Couldn't load jobs (${err.message}). Try refreshing the page.`;
  }
}

companyFilter.addEventListener("change", () => {
  state.company = companyFilter.value;
  applyFilter();
});

entryLevelFilter.addEventListener("change", () => {
  state.entryLevelOnly = entryLevelFilter.checked;
  applyFilter();
});

hideAppliedFilter.addEventListener("change", () => {
  state.hideApplied = hideAppliedFilter.checked;
  applyFilter();
});

// Event delegation - card HTML is inserted via insertAdjacentHTML, so there
// are no per-card listeners to attach; one listener on the shared container
// finds which button was clicked instead.
jobList.addEventListener("click", (e) => {
  const btn = e.target.closest(".mark-applied-btn");
  if (!btn) return;

  const link = btn.dataset.link;
  if (state.appliedLinks.has(link)) {
    state.appliedLinks.delete(link);
  } else {
    state.appliedLinks.add(link);
  }
  saveAppliedLinks(state.appliedLinks);

  if (state.hideApplied) {
    applyFilter();
    return;
  }
  const applied = state.appliedLinks.has(link);
  btn.closest(".job-card").classList.toggle("applied", applied);
  btn.textContent = applied ? "✓ Applied" : "Mark as applied";
});

loadMoreBtn.addEventListener("click", () => renderPage());

document.querySelector(".programs-section").addEventListener("toggle", (e) => {
  if (e.target.open) loadPrograms();
});

loadJobs();
