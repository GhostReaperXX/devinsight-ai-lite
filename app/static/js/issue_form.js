/* Helpful checks while typing. The server still validates everything again. */

const form = document.getElementById("issue-form");
const titleField = document.getElementById("title");
const titleCount = document.getElementById("title-count");

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
