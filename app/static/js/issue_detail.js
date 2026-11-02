/* Change status, add comments and mark duplicates without a full page reload. */

const comments = document.getElementById("comments");
const issueId = comments.dataset.issueId;

const statusActions = document.getElementById("status-actions");
if (statusActions) {
  const statusError = document.getElementById("status-error");
  statusActions.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-status]");
    if (!button) {
      return;
    }
    statusError.textContent = "";
    button.disabled = true;
    try {
      await apiRequest(`/api/issues/${issueId}/status`, {
        method: "PATCH",
        body: { status: button.dataset.status },
      });
      window.location.reload();
    } catch (error) {
      statusError.textContent = error.message;
      button.disabled = false;
    }
  });
}

const commentForm = document.getElementById("comment-form");
const commentError = document.getElementById("comment-error");
commentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  commentError.textContent = "";
  const bodyField = document.getElementById("comment-body");

  try {
    const comment = await apiRequest(`/api/issues/${issueId}/comments`, {
      method: "POST",
      body: { body: bodyField.value },
    });
    document.getElementById("no-comments")?.remove();

    const created = new Date(comment.created_at).toLocaleString();
    const block = createElement("div", { className: "comment border-top py-2" });
    block.append(
      createElement("div", {
        className: "small text-body-secondary",
        text: `${comment.author.full_name}, ${created}`,
      }),
      createElement("div", { className: "comment-body", text: comment.body }),
    );
    comments.append(block);
    bodyField.value = "";
  } catch (error) {
    commentError.textContent = error.message;
  }
});

const relatedList = document.getElementById("related-issues");
if (relatedList) {
  const duplicateError = document.getElementById("duplicate-error");
  relatedList.addEventListener("click", async (event) => {
    const button = event.target.closest("button.mark-duplicate");
    if (!button) {
      return;
    }
    const originalId = Number(button.dataset.originalId);
    if (!window.confirm(`Close this issue as a duplicate of #${originalId}?`)) {
      return;
    }
    duplicateError.textContent = "";
    try {
      await apiRequest(`/api/issues/${issueId}/duplicate`, {
        method: "POST",
        body: { duplicate_of_id: originalId },
      });
      window.location.reload();
    } catch (error) {
      duplicateError.textContent = error.message;
    }
  });
}

document.getElementById("delete-form")?.addEventListener("submit", (event) => {
  if (!window.confirm("Delete this issue permanently?")) {
    event.preventDefault();
  }
});
