// Prep content is hand-curated static JSON, unlike jobs.json which the
// daily scrape regenerates - see frontend/data/*.json for each category.
const HR_QUESTIONS_URL = "data/hr-questions.json";
const RESUME_TIPS_URL = "data/resume-tips.json";

// Same escaping helper as app.js - duplicated rather than shared via a
// module system, since this project deliberately has no build step.
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function questionCardHtml(item) {
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.question)}</p>
      <p class="prep-tip">${escapeHtml(item.tip)}</p>
    </li>
  `;
}

function resumeTipCardHtml(item) {
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.title)}</p>
      <p class="prep-tip">${escapeHtml(item.tip)}</p>
    </li>
  `;
}

// Shared by every prep-hub section (HR questions, resume tips, and
// whatever category gets added next) rather than duplicating the same
// fetch/render/error-handling block per category.
async function loadPrepList(url, listId, cardHtml) {
  const list = document.getElementById(listId);
  if (!list) return;

  list.innerHTML = `<li class="status">Loading...</li>`;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${response.status}`);
    const items = await response.json();
    list.innerHTML = items.map(cardHtml).join("");
  } catch (err) {
    list.innerHTML = `<li class="status">Couldn't load content (${escapeHtml(err.message)}).</li>`;
  }
}

loadPrepList(HR_QUESTIONS_URL, "hr-questions-list", questionCardHtml);
loadPrepList(RESUME_TIPS_URL, "resume-tips-list", resumeTipCardHtml);
