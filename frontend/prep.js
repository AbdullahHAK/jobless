// Prep content is hand-curated static JSON, unlike jobs.json which the
// daily scrape regenerates - see frontend/data/*.json for each category.
const HR_QUESTIONS_URL = "data/hr-questions.json";
const RESUME_TIPS_URL = "data/resume-tips.json";
const COMPANY_QUESTIONS_URL = "data/company-interview-notes.json";
const COLD_EMAIL_TEMPLATES_URL = "data/cold-email-templates.json";
const DSA_TOPICS_URL = "data/dsa-topics.json";
const SQL_CONCEPTS_URL = "data/sql-concepts.json";
const SYSTEM_DESIGN_URL = "data/system-design-topics.json";
const STUDY_NOTES_URL = "data/study-notes.json";

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

function companyQuestionCardHtml(item) {
  const topics = (item.topics || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("");
  return `
    <li class="prep-card company-card">
      <p class="prep-question">${escapeHtml(item.company)}</p>
      <p class="prep-tip">${escapeHtml(item.process)}</p>
      <ul class="company-topics">${topics}</ul>
      <p class="company-note">${escapeHtml(item.note)}</p>
    </li>
  `;
}

// Cold-email templates are kept in memory (rather than round-tripped
// through an HTML data-attribute) so the copy button always copies the
// exact original text, whitespace included.
let coldEmailTemplates = [];

function coldEmailCardHtml(item, index) {
  return `
    <li class="prep-card">
      <div class="cold-email-header">
        <p class="prep-question">${escapeHtml(item.title)}</p>
        <button type="button" class="copy-template-btn" data-index="${index}">Copy</button>
      </div>
      <pre class="cold-email-template">${escapeHtml(item.template)}</pre>
    </li>
  `;
}

function dsaTopicCardHtml(item) {
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.topic)}</p>
      <p class="prep-tip">${escapeHtml(item.note)}</p>
      <a class="prep-card-link" href="${escapeHtml(item.link_url)}" target="_blank" rel="noopener">${escapeHtml(item.link_label)} &rarr;</a>
    </li>
  `;
}

function sqlConceptCardHtml(item) {
  const example = item.example
    ? `<pre class="cold-email-template">${escapeHtml(item.example)}</pre>`
    : "";
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.concept)}</p>
      <p class="prep-tip">${escapeHtml(item.note)}</p>
      ${example}
      <a class="prep-card-link" href="${escapeHtml(item.link_url)}" target="_blank" rel="noopener">${escapeHtml(item.link_label)} &rarr;</a>
    </li>
  `;
}

function systemDesignCardHtml(item) {
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.topic)}</p>
      <p class="prep-tip">${escapeHtml(item.note)}</p>
      <a class="prep-card-link" href="${escapeHtml(item.link_url)}" target="_blank" rel="noopener">${escapeHtml(item.link_label)} &rarr;</a>
    </li>
  `;
}

function studyNoteCardHtml(item) {
  return `
    <li class="prep-card">
      <p class="prep-question">${escapeHtml(item.subject)}</p>
      <p class="prep-tip">${escapeHtml(item.note)}</p>
      <a class="prep-card-link" href="${escapeHtml(item.link_url)}" target="_blank" rel="noopener">${escapeHtml(item.link_label)} &rarr;</a>
    </li>
  `;
}

function skeletonCardsHtml(count) {
  return Array(count).fill('<li class="skeleton-card" aria-hidden="true"></li>').join("");
}

// Shared by every prep-hub section (HR questions, resume tips, and
// whatever category gets added next) rather than duplicating the same
// fetch/render/error-handling block per category.
async function loadPrepList(url, listId, cardHtml) {
  const list = document.getElementById(listId);
  if (!list) return [];

  list.innerHTML = skeletonCardsHtml(3);
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${response.status}`);
    const items = await response.json();
    list.innerHTML = items.map(cardHtml).join("");
    return items;
  } catch (err) {
    list.innerHTML = `<li class="status">Couldn't load content (${escapeHtml(err.message)}).</li>`;
    return [];
  }
}

// Event delegation, same pattern as app.js's mark-applied button - cards
// are inserted via innerHTML, so there's no per-card listener to attach.
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".copy-template-btn");
  if (!btn) return;

  const template = coldEmailTemplates[Number(btn.dataset.index)]?.template;
  if (!template) return;

  const originalLabel = btn.textContent;
  try {
    await navigator.clipboard.writeText(template);
    btn.textContent = "Copied!";
  } catch {
    btn.textContent = "Couldn't copy";
  }
  setTimeout(() => {
    btn.textContent = originalLabel;
  }, 1500);
});

loadPrepList(HR_QUESTIONS_URL, "hr-questions-list", questionCardHtml);
loadPrepList(RESUME_TIPS_URL, "resume-tips-list", resumeTipCardHtml);
loadPrepList(COMPANY_QUESTIONS_URL, "company-questions-list", companyQuestionCardHtml);
loadPrepList(COLD_EMAIL_TEMPLATES_URL, "cold-email-list", coldEmailCardHtml).then((items) => {
  coldEmailTemplates = items;
});
loadPrepList(DSA_TOPICS_URL, "dsa-topics-list", dsaTopicCardHtml);
loadPrepList(SQL_CONCEPTS_URL, "sql-concepts-list", sqlConceptCardHtml);
loadPrepList(SYSTEM_DESIGN_URL, "system-design-list", systemDesignCardHtml);
loadPrepList(STUDY_NOTES_URL, "study-notes-list", studyNoteCardHtml);
