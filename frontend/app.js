// In production this would point at a reverse-proxied /api path on the same
// origin (avoiding CORS entirely); for local dev it just points straight at
// the API's own port.
const API_BASE = window.JOBLESS_API_BASE || "http://localhost:8000";
const PAGE_SIZE = 50;

const state = {
  offset: 0,
  company: "",
};

const jobList = document.getElementById("job-list");
const statusEl = document.getElementById("status");
const resultCount = document.getElementById("result-count");
const loadMoreBtn = document.getElementById("load-more");
const companyFilter = document.getElementById("company-filter");

async function loadCompanyOptions() {
  try {
    const response = await fetch(`${API_BASE}/companies`);
    if (!response.ok) return;
    const companies = await response.json();
    companyFilter.innerHTML =
      `<option value="">All companies</option>` +
      companies.map((c) => `<option value="${c}">${c}</option>`).join("");
  } catch {
    // Filter just stays at "All companies" if this fails - not fatal.
  }
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

async function fetchJobs({ reset = false } = {}) {
  if (reset) {
    state.offset = 0;
    jobList.innerHTML = "";
  }

  statusEl.textContent = "Loading...";
  loadMoreBtn.hidden = true;

  const params = new URLSearchParams({ limit: PAGE_SIZE, offset: state.offset });
  if (state.company) params.set("company", state.company);

  try {
    const response = await fetch(`${API_BASE}/jobs?${params}`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const jobs = await response.json();

    jobList.insertAdjacentHTML("beforeend", jobs.map(jobCardHtml).join(""));

    state.offset += jobs.length;
    resultCount.textContent = `${jobList.children.length} job${jobList.children.length === 1 ? "" : "s"} shown`;
    statusEl.textContent = jobList.children.length === 0 ? "No jobs found." : "";
    loadMoreBtn.hidden = jobs.length < PAGE_SIZE;
  } catch (err) {
    statusEl.textContent = `Couldn't load jobs (${err.message}). Is the API running?`;
  }
}

companyFilter.addEventListener("change", () => {
  state.company = companyFilter.value;
  fetchJobs({ reset: true });
});

loadMoreBtn.addEventListener("click", () => fetchJobs());

loadCompanyOptions();
fetchJobs({ reset: true });
