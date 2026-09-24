// Prep content is hand-curated static JSON, unlike jobs.json which the
// daily scrape regenerates - see frontend/data/*.json for each category.
const HR_QUESTIONS_URL = "data/hr-questions.json";

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

async function loadHrQuestions() {
  const list = document.getElementById("hr-questions-list");
  if (!list) return;

  list.innerHTML = `<li class="status">Loading...</li>`;
  try {
    const response = await fetch(HR_QUESTIONS_URL);
    if (!response.ok) throw new Error(`${response.status}`);
    const questions = await response.json();
    list.innerHTML = questions.map(questionCardHtml).join("");
  } catch (err) {
    list.innerHTML = `<li class="status">Couldn't load questions (${escapeHtml(err.message)}).</li>`;
  }
}

loadHrQuestions();
