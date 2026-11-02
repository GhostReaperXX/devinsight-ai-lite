/* Checks while typing, and live AI suggestions. The server still validates everything again. */

const form = document.getElementById("issue-form");
const titleField = document.getElementById("title");
const titleCount = document.getElementById("title-count");
const descriptionField = document.getElementById("description");
const categoryField = document.getElementById("category");

function updateTitleCount() {
  titleCount.textContent = `${titleField.value.trim().length} of 150.`;
}

titleField.addEventListener("input", updateTitleCount);
updateTitleCount();

form.addEventListener("submit", (event) => {
  if (!form.checkValidity()) {
    event.preventDefault();
    form.classList.add("was-validated");
    form.querySelector(":invalid").focus();
  }
});

/* ---------- AI assistant ---------- */

const hint = document.getElementById("ai-hint");
const suggestionBox = document.getElementById("ai-suggestion");
const relatedBox = document.getElementById("ai-related");
const relatedList = document.getElementById("ai-related-list");
let suggestedCategory = null;
let latestRequest = 0;

function showSuggestion(suggestion) {
  suggestionBox.hidden = suggestion === null;
  if (suggestion === null) {
    return;
  }
  const percent = Math.round(suggestion.confidence * 100);
  suggestedCategory = suggestion.category;
  document.getElementById("ai-category").textContent =
    categoryField.querySelector(`option[value="${suggestion.category}"]`).textContent;
  document.getElementById("ai-meter-fill").style.width = `${percent}%`;
  document.getElementById("ai-meter").setAttribute("aria-label", `Confidence ${percent} percent`);
  document.getElementById("ai-confidence").textContent = `Confidence: ${percent}%`;
  document.getElementById("ai-unsure").hidden = suggestion.is_confident;
}

function showRelated(related) {
  relatedBox.hidden = related.length === 0;
  relatedList.replaceChildren();
  for (const item of related) {
    const link = createElement("a", { className: "text-decoration-none", text: `#${item.id} ${item.title}` });
    link.href = `/issues/${item.id}`;
    link.target = "_blank";
    const row = createElement("li", { className: "mb-2" });
    row.append(
      link,
      createElement("div", {
        className: "text-body-secondary",
        text: `${item.project_key}, similarity ${item.score.toFixed(2)}`,
      }),
    );
    relatedList.append(row);
  }
}

async function analyze() {
  const title = titleField.value.trim();
  const description = descriptionField.value.trim();
  if (title.length + description.length < 15) {
    return;
  }

  // If the person keeps typing, only the newest answer may be shown.
  const requestNumber = ++latestRequest;
  const excludeId = form.dataset.excludeId;
  const answer = await apiRequest("/api/insights/analyze", {
    method: "POST",
    body: { title, description, exclude_issue_id: excludeId ? Number(excludeId) : null },
  });
  if (requestNumber !== latestRequest) {
    return;
  }
  hint.hidden = true;
  showSuggestion(answer.suggestion);
  showRelated(answer.related);
}

/* Debounce: wait until typing pauses, instead of calling the server on every key. */
let typingTimer = null;
function analyzeAfterPause() {
  clearTimeout(typingTimer);
  typingTimer = setTimeout(() => analyze().catch(() => {}), 500);
}

titleField.addEventListener("input", analyzeAfterPause);
descriptionField.addEventListener("input", analyzeAfterPause);
document.getElementById("ai-use").addEventListener("click", () => {
  categoryField.value = suggestedCategory;
  categoryField.focus();
});
analyzeAfterPause();
