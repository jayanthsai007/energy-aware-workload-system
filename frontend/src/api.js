const API_BASE = process.env.REACT_APP_API_BASE || "";

function buildUrl(path) {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
  const route = path.startsWith("/") ? path : `/${path}`;
  return `${base}${route}`;
}

async function fetchJson(path) {
  const response = await fetch(buildUrl(path));

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

export async function fetchDashboardBundle() {
  const [nodes, metrics, executionMetrics, nodeInputs, backgroundActivity] = await Promise.all([
    fetchJson("/active-nodes"),
    fetchJson("/metrics"),
    fetchJson("/execution-metrics").catch(() => []),
    fetchJson("/node-inputs").catch(() => ({})),
    fetchJson("/background-activity").catch(() => null),
  ]);

  return { nodes, metrics, executionMetrics, nodeInputs, backgroundActivity };
}

export async function fetchNodeBundle() {
  const [nodes, metrics, executionMetrics, nodeInputs] = await Promise.all([
    fetchJson("/active-nodes"),
    fetchJson("/metrics"),
    fetchJson("/execution-metrics").catch(() => []),
    fetchJson("/node-inputs").catch(() => ({})),
  ]);

  return { nodes, metrics, executionMetrics, nodeInputs };
}

export async function fetchTaskStatus(taskId) {
  return fetchJson(`/task/${encodeURIComponent(taskId)}`);
}

export async function fetchNodeCompositeScore(nodeId, taskId) {
  const query = taskId ? `?task_id=${encodeURIComponent(taskId)}` : "";
  return fetchJson(`/nodes/${encodeURIComponent(nodeId)}/composite-score${query}`);
}
