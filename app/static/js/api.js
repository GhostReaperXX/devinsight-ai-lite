/* A small helper around fetch(): sends JSON, returns JSON, throws readable errors. */

async function apiRequest(url, { method = "GET", body } = {}) {
  const options = { method, headers: { Accept: "application/json" } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  const data = response.status === 204 ? null : await response.json();

  if (!response.ok) {
    throw new Error(readableError(data));
  }
  return data;
}

/* FastAPI sends "detail" as text for our own errors and as a list for validation errors. */
function readableError(data) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(". ");
  }
  return "Something went wrong. Please try again.";
}

/* Build an element with text only, so user content can never become HTML. */
function createElement(tag, { className = "", text = "" } = {}) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}
