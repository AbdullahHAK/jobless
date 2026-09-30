// The reviews API isn't deployed anywhere publicly reachable yet - see
// README for status. Once it is, set this to that base URL (e.g.
// "https://jobless-api.onrender.com") and both browsing and submission
// switch on automatically - everything below already handles the
// not-yet-configured case gracefully instead of throwing fetch errors at
// visitors.
const API_BASE = "";

// Same escaping helper as app.js/prep.js - duplicated rather than shared
// via a module system, since this project deliberately has no build step.
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function starString(rating) {
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}

function reviewCardHtml(review) {
  const date = new Date(review.submitted_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const roleLine = review.role ? `${escapeHtml(review.role)} · ` : "";
  const statusLine = review.employment_status === "current" ? "Current employee" : "Former employee";
  const salaryLine = review.salary_range
    ? `<p class="review-salary">💰 ${escapeHtml(review.salary_range)}</p>`
    : "";
  return `
    <li class="prep-card review-card">
      <div class="review-card-top">
        <p class="prep-question">${escapeHtml(review.company)}</p>
        <span class="review-stars" aria-label="${review.rating} out of 5 stars">${starString(review.rating)}</span>
      </div>
      <p class="review-meta">${roleLine}${statusLine} · ${date}</p>
      ${salaryLine}
      <p class="review-text">${escapeHtml(review.review_text)}</p>
    </li>
  `;
}

let allReviews = [];

function renderReviews() {
  const list = document.getElementById("reviews-list");
  const status = document.getElementById("reviews-status");
  const filterValue = document.getElementById("review-company-filter").value;
  const filtered = filterValue ? allReviews.filter((r) => r.company === filterValue) : allReviews;

  status.textContent = filtered.length === 0 ? "No reviews yet - be the first to share yours above." : "";
  list.innerHTML = filtered.map(reviewCardHtml).join("");
}

async function loadReviews() {
  const list = document.getElementById("reviews-list");
  const status = document.getElementById("reviews-status");
  if (!list) return;

  if (!API_BASE) {
    status.textContent =
      "Reviews are launching soon - the backend that stores and moderates them is still being deployed. Check back soon.";
    return;
  }

  status.textContent = "";
  list.innerHTML = Array(3).fill('<li class="skeleton-card" aria-hidden="true"></li>').join("");
  try {
    const response = await fetch(`${API_BASE}/reviews`);
    if (!response.ok) throw new Error(`${response.status}`);
    allReviews = await response.json();

    const filter = document.getElementById("review-company-filter");
    const companies = [...new Set(allReviews.map((r) => r.company))].sort();
    filter.innerHTML =
      `<option value="">All companies</option>` +
      companies.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");

    renderReviews();
  } catch (err) {
    list.innerHTML = "";
    status.textContent = `Couldn't load reviews (${err.message}). Try refreshing the page.`;
  }
}

// Disables the submission form entirely (rather than letting people fill
// it out and only finding out on submit) when the API isn't configured yet.
function initFormAvailability() {
  const form = document.getElementById("review-form");
  const statusEl = document.getElementById("review-form-status");
  if (!form || API_BASE) return;

  for (const el of form.elements) el.disabled = true;
  statusEl.textContent =
    "Submissions aren't open yet - the backend that stores and moderates reviews is still being deployed. Check back soon.";
}

document.getElementById("review-company-filter")?.addEventListener("change", renderReviews);

document.getElementById("review-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const statusEl = document.getElementById("review-form-status");
  const submitBtn = e.target.querySelector(".submit-review-btn");

  if (!API_BASE) {
    statusEl.textContent = "Submissions aren't open yet - check back soon.";
    return;
  }

  const body = {
    company: document.getElementById("review-company").value.trim(),
    role: document.getElementById("review-role").value.trim() || null,
    employment_status: document.getElementById("review-employment-status").value,
    rating: Number(document.getElementById("review-rating").value),
    salary_range: document.getElementById("review-salary").value.trim() || null,
    review_text: document.getElementById("review-text").value.trim(),
  };

  submitBtn.disabled = true;
  statusEl.textContent = "Submitting...";
  try {
    const response = await fetch(`${API_BASE}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.status === 429) throw new Error("Too many submissions from this browser - try again later.");
    if (!response.ok) throw new Error("Please check your review meets the minimum length and try again.");

    statusEl.textContent = "Thanks! Your review is pending moderation and will appear once approved.";
    e.target.reset();
  } catch (err) {
    statusEl.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

initFormAvailability();
loadReviews();
