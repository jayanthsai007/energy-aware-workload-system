import { useEffect, useMemo, useState } from "react";
import { fetchDashboardBundle, fetchNodeCompositeScore } from "../api";
import DashboardNodePanel from "../components/DashboardNodePanel";
import StatCard from "../components/StatCard";
import { buildHistory, createNodeCards } from "../utils";

function getRecentExecutionInput(executionMetrics) {
  const latestExecution = (executionMetrics || []).find(
    (entry) => entry.task_id && entry.script
  );

  if (!latestExecution) {
    return null;
  }

  return {
    task_id: latestExecution.task_id,
    script: latestExecution.script,
    language: latestExecution.language,
    status: "completed",
    created_at: latestExecution.timestamp,
    assignedNodeId: latestExecution.node_id,
  };
}

function getRecentNodeInput(nodeInputs, executionMetrics) {
  const inputs = Object.entries(nodeInputs || {})
    .map(([nodeId, input]) => ({
      ...input,
      assignedNodeId: nodeId,
    }))
    .filter((input) => input.task_id);

  if (!inputs.length) {
    return getRecentExecutionInput(executionMetrics);
  }

  const runningInput = inputs
    .filter((input) => String(input.status || "").toLowerCase() === "running")
    .sort((left, right) => new Date(right.created_at || 0) - new Date(left.created_at || 0))[0];

  if (runningInput) {
    return runningInput;
  }

  return inputs.sort((left, right) => new Date(right.created_at || 0) - new Date(left.created_at || 0))[0];
}

function formatInputLanguage(recentInput) {
  if (!recentInput?.language) {
    return "Not available";
  }

  const normalizedLanguage = String(recentInput.language).trim().toLowerCase();

  if (!normalizedLanguage) {
    return "Not available";
  }

  return normalizedLanguage.charAt(0).toUpperCase() + normalizedLanguage.slice(1);
}

function getRecentInputScriptPreview(recentInput) {
  const script = recentInput?.script;

  if (!script || !String(script).trim()) {
    return "Not available";
  }

  const compactScript = String(script).replace(/\s+/g, " ").trim();

  if (compactScript.length <= 100) {
    return compactScript;
  }

  return `${compactScript.slice(0, 97)}...`;
}

function formatBackgroundActivity(activity) {
  if (!activity?.message) {
    return {
      value: "Waiting for backend activity",
      subtitle: "No heartbeat, metrics, or scheduler update available yet.",
      accent: "neutral",
    };
  }

  const queueSize = Number(activity.queue_size) || 0;
  const detailParts = [activity.details].filter(Boolean);

  if (queueSize > 0) {
    detailParts.push(`${queueSize} task${queueSize === 1 ? "" : "s"} in queue`);
  }

  return {
    value: activity.message,
    subtitle: detailParts.join(" | "),
    accent:
      activity.level === "error"
        ? "danger"
        : activity.level === "warning"
          ? "danger"
          : "neutral",
  };
}

export default function Dashboard() {
  const [nodes, setNodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [executionMetrics, setExecutionMetrics] = useState([]);
  const [nodeInputs, setNodeInputs] = useState({});
  const [backgroundActivity, setBackgroundActivity] = useState(null);
  const [schedulerScores, setSchedulerScores] = useState([]);
  const [error, setError] = useState("");
  const [taskIdSearch, setTaskIdSearch] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const bundle = await fetchDashboardBundle();

        if (cancelled) {
          return;
        }

        setNodes(bundle.nodes || []);
        setMetrics(bundle.metrics || []);
        setExecutionMetrics(bundle.executionMetrics || []);
        setNodeInputs(bundle.nodeInputs || {});
        setBackgroundActivity(bundle.backgroundActivity || null);
        setError("");
      } catch (loadError) {
        if (!cancelled) {
          setError("Unable to connect to backend metrics. Start the backend on http://127.0.0.1:8000.");
        }
      }
    }

    loadDashboard();
    const intervalId = window.setInterval(loadDashboard, 2000);

    // WebSocket connection for real-time updates
    const wsUrl = process.env.REACT_APP_WS_BASE || "ws://127.0.0.1:8000/ws";
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log("WebSocket connected");
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "metrics") {
          const newMetric = {
            node_id: message.data.node_id,
            cpu: message.data.cpu,
            memory: message.data.memory,
            temperature: message.data.temperature,
            timestamp: new Date().toISOString()
          };
          setMetrics(prevMetrics => {
            const updated = [newMetric, ...prevMetrics].slice(0, 50); // Keep last 50
            return updated;
          });
        }
      } catch (e) {
        console.error("WebSocket message error:", e);
      }
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    websocket.onclose = () => {
      console.log("WebSocket closed");
    };
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  const history = useMemo(() => buildHistory(metrics), [metrics]);
  const nodeCards = useMemo(() => createNodeCards(nodes, history), [nodes, history]);
  const recentInput = useMemo(
    () => getRecentNodeInput(nodeInputs, executionMetrics),
    [executionMetrics, nodeInputs]
  );
  const recentInputType = useMemo(() => formatInputLanguage(recentInput), [recentInput]);
  const recentInputScript = useMemo(() => getRecentInputScriptPreview(recentInput), [recentInput]);
  const backgroundActivityCard = useMemo(
    () => formatBackgroundActivity(backgroundActivity),
    [backgroundActivity]
  );
  const selectedTaskId = taskIdSearch.trim() || recentInput?.task_id || "";

  const activeNodes = nodes.filter((node) =>
    String(node.status || "").toLowerCase() === "active" ||
    String(node.status || "").toLowerCase() === "online"
  ).length;
  const optimalNodeId = useMemo(() => {
    const rankedScores = schedulerScores.filter((entry) => Number.isFinite(entry.schedulerScore));
    if (!rankedScores.length) {
      return "";
    }

    return rankedScores.reduce(
      (bestEntry, currentEntry) =>
        currentEntry.schedulerScore < bestEntry.schedulerScore ? currentEntry : bestEntry,
      rankedScores[0]
    ).nodeId;
  }, [schedulerScores]);

  useEffect(() => {
    let cancelled = false;

    async function loadSchedulerScores() {
      const activeNodeIds = nodes
        .map((node) => node.node_id)
        .filter(Boolean);

      if (!activeNodeIds.length || !selectedTaskId) {
        setSchedulerScores([]);
        return;
      }

      const results = await Promise.all(
        activeNodeIds.map(async (nodeId) => {
          try {
            const response = await fetchNodeCompositeScore(nodeId, selectedTaskId);

            return {
              nodeId,
              schedulerScore: Number(response?.composite_score),
            };
          } catch (scoreError) {
            return {
              nodeId,
              schedulerScore: null,
            };
          }
        })
      );

      if (!cancelled) {
        setSchedulerScores(results);
      }
    }

    loadSchedulerScores();

    return () => {
      cancelled = true;
    };
  }, [nodes, selectedTaskId]);

  function handleTaskSearchSubmit(event) {
    event.preventDefault();
  }

  return (
    <main className="screen-shell">
      <div className="screen-overlay" />

      <section className="screen-content">
        <header className="topbar">
          <div className="topbar-left">
            <button className="icon-button" type="button" aria-label="Menu">
              <span />
              <span />
              <span />
            </button>
            <div className="page-title">Energy-Aware Workload System</div>
          </div>

          <div className="topbar-actions">
            <button className="toolbar-button" type="button" aria-label="Layout">
              ||
            </button>
            <button className="toolbar-button" type="button" aria-label="Grid">
              []
            </button>
          </div>
        </header>

        {error ? <div className="error-banner panel">{error}</div> : null}

        <section className="dashboard-grid dashboard-nodes">
          {nodeCards.map((node) => (
            <DashboardNodePanel
              key={node.node_id}
              node={node}
              chartData={node.chartData}
              cpuValue={node.cpuValue}
              temperature={node.temperatureText}
              power={node.powerText}
              voltage={node.voltageText}
              tone={node.tone}
            />
          ))}
        </section>

        <section className="dashboard-grid dashboard-stats">
          <StatCard
            icon="!"
            title="Backend Activity"
            value={backgroundActivityCard.value}
            subtitle={backgroundActivityCard.subtitle}
            accent={backgroundActivityCard.accent}
          />
          <StatCard
            icon="#"
            title="Nodes Registered"
            value={`${nodes.length} Total Nodes`}
            accent="neutral"
          />
          <StatCard
            icon="+"
            title="Nodes active"
            value={`${activeNodes} Total Nodes`}
            accent="neutral"
          />
        </section>

        <section className="dashboard-bottom">
          <div className="panel chart-panel">
            <div className="chart-header">
              <div className="chart-title">
                <span>Scheduler Scores</span>
                <span className="status-dot" />
              </div>
              <div className="chart-header-actions">
                <span>::</span>
                <span>o</span>
              </div>
            </div>

            <div className="scheduler-score-table-wrap">
              <table className="scheduler-score-table">
                <thead>
                  <tr>
                    <th>Node ID</th>
                    <th>Scheduler Score</th>
                    <th>Optimal</th>
                  </tr>
                </thead>
                <tbody>
                  {schedulerScores.length ? (
                    schedulerScores.map((entry) => (
                      <tr key={entry.nodeId} className={entry.nodeId === optimalNodeId ? "is-optimal" : ""}>
                        <td>{entry.nodeId}</td>
                        <td>
                          {Number.isFinite(entry.schedulerScore)
                            ? entry.schedulerScore.toFixed(4)
                            : "Not available"}
                        </td>
                        <td className="scheduler-score-status">
                          {entry.nodeId === optimalNodeId ? <span className="optimal-node-tick">✓</span> : ""}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="3" className="scheduler-score-empty">
                        {selectedTaskId
                          ? "Scheduler scores are not available for the selected task yet."
                          : "No task is available yet to compute scheduler scores."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <aside className="panel info-panel">
            <div className="panel-info">i</div>
            <h3 className="info-panel-title">Input</h3>
            <form className="dashboard-task-search" onSubmit={handleTaskSearchSubmit}>
              <input
                className="dashboard-task-search-input"
                type="text"
                value={taskIdSearch}
                onChange={(event) => setTaskIdSearch(event.target.value)}
                placeholder="Search by task id"
                aria-label="Search by task id"
              />
              <button className="dashboard-task-search-button" type="submit">
                Search
              </button>
            </form>
            <div className="file-card">
              <div className="file-icon">[]</div>
              <div>
                <div className="file-name">Input Type: {recentInputType}</div>
                <div className="file-subtext">Input Script: {recentInputScript}</div>
              </div>
            </div>
            <div className="info-list">
              <div>Latest backend sync: {history[history.length - 1]?.label || "--:--"}</div>
              <div>Task ID: {recentInput?.task_id || "Not available"}</div>
              <div>Node ID: {recentInput?.assignedNodeId || "Not available"}</div>
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}
