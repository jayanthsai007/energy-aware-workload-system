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
  const [nodes, metrics, executionMetrics] = await Promise.all([
    fetchJson("/nodes"),
    fetchJson("/metrics"),
    fetchJson("/execution-metrics").catch(() => []),
  ]);

  return { nodes, metrics, executionMetrics };
}

export async function fetchNodeBundle() {
  const [nodes, metrics, executionMetrics] = await Promise.all([
    fetchJson("/nodes"),
    fetchJson("/metrics"),
    fetchJson("/execution-metrics").catch(() => []),
  ]);

  return { nodes, metrics, executionMetrics };
}
