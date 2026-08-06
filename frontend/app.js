// Job listings are a static file regenerated daily by GitHub Actions and
// committed back into the repo - no backend needed to browse jobs at all.
const JOBS_DATA_URL = "data/jobs.json";
const PAGE_SIZE = 50;

// Matches job titles aimed at recent grads - the audience this portal is
// increasingly focused on, alongside general listings.
const ENTRY_LEVEL_PATTERN = /\b(intern(ship)?|graduate|entry[- ]level|fresh(er)?|trainee)\b/i;

const state = {
  allJobs: [],
  filtered: [],
  shown: 0,
  company: "",
  entryLevelOnly: false,
};

const jobList = document.getElementById("job-list");
const statusEl = document.getElementById("status");
const resultCount = document.getElementById("result-count");
const loadMoreBtn = document.getElementById("load-more");
const companyFilter = document.getElementById("company-filter");
const entryLevelFilter = document.getElementById("entry-level-filter");

function populateCompanyOptions() {
  const companies = [...new Set(state.allJobs.map((j) => j.company))].sort();
  companyFilter.innerHTML =
    `<option value="">All companies</option>` +
    companies.map((c) => `<option value="${c}">${c}</option>`).join("");
}

function jobCardHtml(job) {
  const date = new Date(job.date_scraped).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  return `
    <li class="job-card">
      <a class="job-title" href="${job.apply_link}" target="_blank" rel="noopener">${job.title}</a>
      <div class="job-meta">${job.company} · ${job.location} · seen ${date}</div>
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

loadMoreBtn.addEventListener("click", () => renderPage());

loadJobs();
