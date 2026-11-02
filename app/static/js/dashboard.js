/* Refresh the dashboard numbers without reloading the page. */

const projectFilter = document.getElementById("project-filter");

function renderBars(containerId, counts) {
  const container = document.getElementById(containerId);
  const labels = JSON.parse(container.dataset.labels);
  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);
  container.replaceChildren();

  for (const [value, label] of Object.entries(labels)) {
    const count = counts[value] ?? 0;
    const percent = total === 0 ? 0 : Math.round((count / total) * 100);

    const row = createElement("div", { className: "bar-row" });
    const track = createElement("div", { className: "progress" });
    const fill = createElement("div", { className: "progress-bar" });
    fill.style.width = `${percent}%`;
    track.setAttribute("role", "img");
    track.setAttribute("aria-label", `${label}: ${count} issues, ${percent} percent`);
    track.append(fill);

    row.append(
      createElement("div", { className: "bar-label", text: label }),
      track,
      createElement("div", { className: "bar-count", text: String(count) }),
    );
    container.append(row);
  }
}

function renderUrgent(issues) {
  const tbody = document.getElementById("urgent-issues");
  tbody.replaceChildren();

  if (issues.length === 0) {
    const row = createElement("tr");
    const cell = createElement("td", { className: "text-body-secondary", text: "Nothing urgent. Well done." });
    cell.colSpan = 5;
    row.append(cell);
    tbody.append(row);
    return;
  }

  for (const issue of issues) {
    const row = createElement("tr");
    const link = createElement("a", { className: "text-decoration-none", text: issue.title });
    link.href = `/issues/${issue.id}`;
    const titleCell = createElement("td");
    titleCell.append(link);

    const priority = createElement("span", { className: `badge badge-priority-${issue.priority}`, text: issue.priority });
    const status = createElement("span", { className: `badge badge-status-${issue.status}`, text: issue.status.replace("_", " ") });
    const priorityCell = createElement("td");
    priorityCell.append(priority);
    const statusCell = createElement("td");
    statusCell.append(status);

    row.append(
      createElement("td", { className: "text-body-secondary", text: `#${issue.id}` }),
      titleCell,
      createElement("td", { text: issue.project.key }),
      priorityCell,
      statusCell,
    );
    tbody.append(row);
  }
}

async function refreshDashboard() {
  const projectId = projectFilter.value;
  const projectQuery = projectId ? `&project_id=${projectId}` : "";

  const [stats, open, inProgress] = await Promise.all([
    apiRequest(`/api/stats?${projectQuery.slice(1)}`),
    apiRequest(`/api/issues?status=open&sort=priority&limit=6${projectQuery}`),
    apiRequest(`/api/issues?status=in_progress&sort=priority&limit=6${projectQuery}`),
  ]);

  const byStatus = stats.by_status;
  document.getElementById("kpi-total").textContent = stats.total;
  document.getElementById("kpi-open").textContent = byStatus.open ?? 0;
  document.getElementById("kpi-progress").textContent = byStatus.in_progress ?? 0;
  document.getElementById("kpi-done").textContent = (byStatus.resolved ?? 0) + (byStatus.closed ?? 0);

  renderBars("chart-status", stats.by_status);
  renderBars("chart-category", stats.by_category);
  renderBars("chart-priority", stats.by_priority);

  const rank = { critical: 0, high: 1, medium: 2, low: 3 };
  const urgent = [...open.items, ...inProgress.items]
    .sort((a, b) => rank[a.priority] - rank[b.priority])
    .slice(0, 6);
  renderUrgent(urgent);
}

projectFilter.addEventListener("change", refreshDashboard);
refreshDashboard();
