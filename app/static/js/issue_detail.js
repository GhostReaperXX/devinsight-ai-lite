/* Change status and add comments on the issue page without a full reload. */

const statusActions = document.getElementById("status-actions");
const statusError = document.getElementById("status-error");
const commentForm = document.getElementById("comment-form");
const commentError = document.getElementById("comment-error");
const comments = document.getElementById("comments");
const issueId = comments.dataset.issueId;

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

commentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  commentError.textContent = "";
  const bodyField = document.getElementById("comment-body");
  const authorField = document.getElementById("comment-author");

  try {
    const comment = await apiRequest(`/api/issues/${issueId}/comments`, {
      method: "POST",
      body: { author_id: Number(authorField.value), body: bodyField.value },
    });
    document.getElementById("no-comments")?.remove();

    const created = new Date(comment.created_at + "Z").toLocaleString();
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

document.getElementById("delete-form").addEventListener("submit", (event) => {
  if (!window.confirm("Delete this issue permanently?")) {
    event.preventDefault();
  }
});
