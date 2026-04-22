import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchNodeBundle, fetchNodeCompositeScore, fetchTaskStatus } from "../api";
import Gauge from "../components/Gauge";
import LineChartComponent from "../components/LineChart";
import MiniChart from "../components/MiniChart";
import {
  average,
  buildHistory,
  createNodeCards,
  getNodeHistory,
} from "../utils";

function MetricBadge({ label, value }) {
  return (
    <div className="metric-badge panel">
      <span className="metric-badge-icon">*</span>
      <span className="metric-badge-label">{label}</span>
      <span className="metric-badge-value">{value}</span>
    </div>
  );
}

function getNodeInputPreview(nodeInputs, nodeId) {
  const rawInput = nodeInputs?.[nodeId]?.script;

  if (!rawInput || !rawInput.trim()) {
    return "Input not given";
  }

  const compactInput = rawInput.replace(/\s+/g, " ").trim();

  if (compactInput.length <= 120) {
    return compactInput;
  }

  return `${compactInput.slice(0, 117)}...`;
}

function getLatestExecutionForNode(executionMetrics, nodeId) {
  return (executionMetrics || []).find(
    (entry) => entry.node_id === nodeId && entry.script
  ) || null;
}

function getNodeInputDetails(nodeInputs, executionMetrics, nodeId) {
  const liveInput = nodeInputs?.[nodeId];
  if (liveInput?.script) {
    return liveInput;
  }

  const latestExecution = getLatestExecutionForNode(executionMetrics, nodeId);
  if (!latestExecution) {
    return null;
  }

  return {
    task_id: latestExecution.task_id,
    script: latestExecution.script,
    language: latestExecution.language,
    status: "completed",
    created_at: latestExecution.timestamp,
  };
}

function getNodeDisplayName(nodeCards, nodeId) {
  const matchedNode = nodeCards.find((node) => node.node_id === nodeId);
  return matchedNode?.label || "Not available";
}

function formatMemoryAmount(value) {
  return `${(Number(value) || 0).toFixed(1)} GB`;
}

function formatExecutionSeconds(value) {
  const seconds = Number(value);

  if (!Number.isFinite(seconds) || seconds < 0) {
    return "Not available";
  }

  return `${seconds.toFixed(2)} sec`;
}

function getTaskElapsedSeconds(taskDetails, currentTimeMs) {
  const createdAtMs = Date.parse(taskDetails?.created_at || "");

  if (!Number.isFinite(createdAtMs)) {
    return null;
  }

  return Math.max(0, (currentTimeMs - createdAtMs) / 1000);
}

function getExecutionCardDetails(executionMetrics, nodeId, taskDetails, currentTimeMs) {
  const nodeMetrics = executionMetrics.filter((entry) => entry.node_id === nodeId);
  const latestMetric = nodeMetrics[0] || null;
  const runtimeValues = nodeMetrics
    .map((entry) => Number(entry.execution_time))
    .filter((value) => Number.isFinite(value) && value >= 0);
  const normalizedStatus = String(taskDetails?.status || "").toLowerCase();
  const isLiveTask = normalizedStatus === "running" || normalizedStatus === "queued";
  const liveRuntimeSeconds = isLiveTask
    ? getTaskElapsedSeconds(taskDetails, currentTimeMs)
    : Number(taskDetails?.execution_time);
  const hasLiveRuntime = Number.isFinite(liveRuntimeSeconds) && liveRuntimeSeconds >= 0;
  const chartData = nodeMetrics.length
    ? [...nodeMetrics]
        .slice()
        .reverse()
        .map((entry, index) => ({
          label: index % 2 === 0 ? `Run ${index + 1}` : "",
          value: Number(entry.execution_time) || 0,
        }))
    : [{ label: "Run 1", value: 0 }];

  if (hasLiveRuntime) {
    chartData.push({
      label: isLiveTask ? "Live" : `Run ${chartData.length + 1}`,
      value: liveRuntimeSeconds,
    });
  }

  return {
    currentRuntime: hasLiveRuntime
      ? formatExecutionSeconds(liveRuntimeSeconds)
      : latestMetric
        ? formatExecutionSeconds(latestMetric.execution_time)
        : "Not available",
    averageRuntime: runtimeValues.length ? formatExecutionSeconds(average(runtimeValues)) : "Not available",
    chartData,
    description: isLiveTask ? "Live task execution" : "Backend Execution History",
  };
}

function getMemoryUsageExplanation({ usedMemoryGb, availableMemoryGb, memoryPercent, taskStatus, inputPreview }) {
  const normalizedStatus = String(taskStatus || "").toLowerCase();
  const previewAvailable = inputPreview && inputPreview !== "Input not given";

  if (normalizedStatus === "running") {
    return `The backend reports ${memoryPercent.toFixed(1)}% memory usage because this node is actively executing${previewAvailable ? ` the current script: ${inputPreview}` : " the current workload"}.`;
  }

  if (normalizedStatus === "pending") {
    return `The backend reports ${memoryPercent.toFixed(1)}% memory usage while the node keeps roughly ${formatMemoryAmount(usedMemoryGb)} reserved and waits to start the queued task.`;
  }

  if (usedMemoryGb <= 0.1) {
    return "The backend is currently reporting almost no application memory load on this node.";
  }

  return `About ${formatMemoryAmount(usedMemoryGb)} is in use and ${formatMemoryAmount(availableMemoryGb)} remains available, which suggests the memory is mainly being used by the node runtime, recent task data, and normal background services.`;
}

/* function getCompositeScoreDetailsLegacy(executionMetrics, nodeId) {
  const latestNodeMetric = executionMetrics.find((entry) => entry.node_id === nodeId) || null;
  const compositeScore = Number(latestNodeMetric?.composite_score);
  const executionTime = Number(latestNodeMetric?.execution_time) || 0;
  const scoreAvailable = Number.isFinite(compositeScore) && compositeScore > 0;

  if (!latestNodeMetric || !scoreAvailable) {
    return {
      scoreText: "Not available",
      formulaText: "Composite Score = 0.6 × Execution Time + 0.4 × Energy",
      explanation:
        "This node does not yet have a stored composite score from the backend, so the UI can only show the formula used by the training pipeline.",
    };
  }

  const estimatedEnergy = Math.max(0, (compositeScore - 0.6 * executionTime) / 0.4);

  return {
    scoreText: compositeScore.toFixed(2),
    formulaText: `Composite Score = 0.6 × ${executionTime.toFixed(2)} + 0.4 × ${estimatedEnergy.toFixed(2)}`,
    explanation: `The latest backend result for this node produced a composite score of ${compositeScore.toFixed(2)}. The score is weighted more toward execution time, while the remaining portion reflects estimated energy impact.`,
  };
}

function getCompositeScoreDetails(executionMetrics, nodeId) {
  const latestNodeMetric = executionMetrics.find((entry) => entry.node_id === nodeId) || null;
  const compositeScore = Number(latestNodeMetric?.composite_score);
  const scoreAvailable = Number.isFinite(compositeScore);

  if (!latestNodeMetric || !scoreAvailable) {
    return {
      scoreText: "Not available",
      formulaText: "Composite Score = 0.6 x Execution Time + 0.4 x Energy",
      explanation:
        "This node does not yet have a stored composite score from the backend, so the UI can only show the formula used by the training pipeline.",
    };
  }

  return {
    scoreText: compositeScore.toFixed(2),
    formulaText: "Composite Score = 0.6 x Execution Time + 0.4 x Energy",
    explanation: `The latest backend result for this node produced a composite score of ${compositeScore.toFixed(2)}. The score is weighted more toward execution time, while the remaining portion reflects energy impact.`,
  };
}

*/
function getRealtimeCompositeScoreDetails({ nodeId, executionMetrics, taskDetails, powerChart }) {
  const latestNodeMetric = executionMetrics.find((entry) => entry.node_id === nodeId) || null;
  const runtimeSeconds = Number(taskDetails?.execution_time);
  const fallbackRuntimeSeconds = Number(latestNodeMetric?.execution_time);
  const resolvedRuntimeSeconds = Number.isFinite(runtimeSeconds) && runtimeSeconds > 0
    ? runtimeSeconds
    : Number.isFinite(fallbackRuntimeSeconds) && fallbackRuntimeSeconds > 0
      ? fallbackRuntimeSeconds
      : 0;
  const livePowerValues = powerChart
    .map((entry) => Number(entry.value))
    .filter((value) => Number.isFinite(value) && value >= 0);
  const averagePower = livePowerValues.length ? average(livePowerValues) : 0;
  const estimatedEnergy = averagePower * resolvedRuntimeSeconds;
  const compositeScore = 0.6 * resolvedRuntimeSeconds + 0.4 * estimatedEnergy;

  if (resolvedRuntimeSeconds <= 0) {
    return {
      scoreText: "Not available",
      scoreLabel: "Frontend Composite Estimate For",
      formulaText: "Composite Score = 0.6 x Execution Time + 0.4 x Energy",
      explanation: "Needs task runtime to estimate the composite score.",
      note: "This fallback is only a frontend estimate. Optimal-node selection still uses backend scheduler score.",
    };
  }

  return {
    scoreText: compositeScore.toFixed(2),
    scoreLabel: "Frontend Composite Estimate For",
    formulaText: "Composite Score = 0.6 x Execution Time + 0.4 x Energy",
    explanation: `Estimate from ${averagePower.toFixed(2)} W average power and ${resolvedRuntimeSeconds.toFixed(2)} sec runtime.`,
    note: "This explains efficiency behavior, but the backend still picks the optimal node using scheduler score.",
  };
}

function getBackendCompositeScoreDetails(scoreResponse) {
  const score = Number(scoreResponse?.composite_score);
  const modelScore = Number(scoreResponse?.model_score);
  const cpuAdjustment = Number(scoreResponse?.cpu_adjustment);
  const metricsWindow = Number(scoreResponse?.metrics_window);

  if (!Number.isFinite(score)) {
    return null;
  }

  return {
    scoreText: score.toFixed(4),
    scoreLabel: "Backend Scheduler Score For",
    formulaText:
      Number.isFinite(modelScore) && Number.isFinite(cpuAdjustment)
        ? `scheduler_score = ${modelScore.toFixed(4)} + ${cpuAdjustment.toFixed(4)}`
        : "scheduler_score = ml_model_score + (cpu_avg x 0.05)",
    explanation:
      Number.isFinite(modelScore) && Number.isFinite(cpuAdjustment)
        ? `ML score ${modelScore.toFixed(4)} + CPU penalty ${cpuAdjustment.toFixed(4)} = final scheduler score ${score.toFixed(4)}.`
        : "Computed by the backend scheduler for this node and task.",
    note:
      "Composite score teaches the model expected efficiency. Scheduler score adds a live CPU penalty of 0.0000 to 0.0500, is not fixed to 0-1, and the lowest score wins." +
      (Number.isFinite(metricsWindow) ? ` Based on ${metricsWindow} recent metric samples.` : ""),
  };
}

export default function NodeDetails() {
  const { id } = useParams();
  const [nodes, setNodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [executionMetrics, setExecutionMetrics] = useState([]);
  const [nodeInputs, setNodeInputs] = useState({});
  const [error, setError] = useState("");
  const [taskDetails, setTaskDetails] = useState(null);
  const [compositeScoreResponse, setCompositeScoreResponse] = useState(null);
  const [currentTimeMs, setCurrentTimeMs] = useState(() => Date.now());

  useEffect(() => {
    let cancelled = false;

    async function loadDetails() {
      try {
        const bundle = await fetchNodeBundle();

        if (cancelled) {
          return;
        }

        setNodes(bundle.nodes || []);
        setMetrics(bundle.metrics || []);
        setExecutionMetrics(bundle.executionMetrics || []);
        setNodeInputs(bundle.nodeInputs || {});
        setError("");
      } catch (loadError) {
        if (!cancelled) {
          setError("Unable to load backend data for the node details screen.");
        }
      }
    }

    loadDetails();
    const intervalId = window.setInterval(loadDetails, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [id]);

  const history = useMemo(() => buildHistory(metrics), [metrics]);
  const nodeCards = useMemo(() => createNodeCards(nodes, history), [nodes, history]);
  const selectedNode = nodeCards.find((node) => node.node_id === id) || nodeCards[0];
  const selectedNodeHistory = useMemo(
    () => getNodeHistory(metrics, selectedNode?.node_id),
    [metrics, selectedNode]
  );
  const executionCardDetails = useMemo(
    () => getExecutionCardDetails(executionMetrics, selectedNode?.node_id, taskDetails, currentTimeMs),
    [currentTimeMs, executionMetrics, selectedNode, taskDetails]
  );
  const latest = selectedNodeHistory[selectedNodeHistory.length - 1] || {
    cpu: 0,
    memory: 0,
    temperature: 0,
    power: 0,
    network: 0,
  };

  const resourceChart = selectedNodeHistory.map((entry) => ({ label: entry.label, value: entry.cpu }));
  const powerChart = selectedNodeHistory.map((entry) => ({ label: entry.label, value: entry.power }));
  const cpuChart = selectedNodeHistory.map((entry) => ({ label: entry.label, value: entry.cpu }));
  const temperatureChart = selectedNodeHistory.map((entry) => ({ label: entry.label, value: entry.temperature }));
  const executionChart = executionCardDetails.chartData;
  const selectedNodeInput = useMemo(
    () => getNodeInputDetails(nodeInputs, executionMetrics, selectedNode?.node_id),
    [executionMetrics, nodeInputs, selectedNode]
  );

  const networkText = `${latest.network.toFixed(0)} KB/s`;
  const networkInputText = selectedNodeInput?.script
    ? getNodeInputPreview({ [selectedNode?.node_id]: selectedNodeInput }, selectedNode?.node_id)
    : "Input not given";
  const selectedTaskId = selectedNodeInput?.task_id || "";
  const taskStatus = taskDetails?.status || selectedNodeInput?.status || "Not available";
  const taskNodeId = taskDetails?.assigned_node || (selectedTaskId ? selectedNode?.node_id : "") || "Not available";
  const taskNodeName = getNodeDisplayName(nodeCards, taskNodeId);
  const taskExecutionTime = taskDetails?.execution_time != null ? `${taskDetails.execution_time} sec` : "Not available";
  const totalMemoryGb = Number(selectedNode?.totalMemory) || 0;
  const memoryPercent = Math.max(0, Math.min(100, Number(latest.memory) || 0));
  const usedMemoryGb = totalMemoryGb ? (totalMemoryGb * memoryPercent) / 100 : 0;
  const availableMemoryGb = Math.max(0, totalMemoryGb - usedMemoryGb);
  const memoryExplanation = getMemoryUsageExplanation({
    usedMemoryGb,
    availableMemoryGb,
    memoryPercent,
    taskStatus,
    inputPreview: networkInputText,
  });
  const compositeScoreDetails = useMemo(
    () =>
      getBackendCompositeScoreDetails(compositeScoreResponse) ||
      getRealtimeCompositeScoreDetails({
        nodeId: selectedNode?.node_id,
        executionMetrics,
        taskDetails,
        powerChart,
      }),
    [compositeScoreResponse, executionMetrics, powerChart, selectedNode, taskDetails]
  );

  useEffect(() => {
    const normalizedStatus = String(taskDetails?.status || "").toLowerCase();

    if (normalizedStatus !== "running" && normalizedStatus !== "queued") {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setCurrentTimeMs(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [taskDetails]);

  useEffect(() => {
    let cancelled = false;

    async function loadTaskDetails() {
      if (!selectedTaskId) {
        setTaskDetails(null);
        return;
      }

      try {
        const response = await fetchTaskStatus(selectedTaskId);

        if (!cancelled) {
          setTaskDetails(response);
        }
      } catch (taskError) {
        if (!cancelled) {
          setTaskDetails(null);
        }
      }
    }

    loadTaskDetails();
    const intervalId = window.setInterval(loadTaskDetails, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [selectedTaskId]);

  useEffect(() => {
    let cancelled = false;

    async function loadCompositeScore() {
      if (!selectedNode?.node_id) {
        setCompositeScoreResponse(null);
        return;
      }

      try {
        const response = await fetchNodeCompositeScore(selectedNode.node_id, selectedTaskId);

        if (!cancelled) {
          setCompositeScoreResponse(response);
        }
      } catch (scoreError) {
        if (!cancelled) {
          setCompositeScoreResponse(null);
        }
      }
    }

    loadCompositeScore();

    return () => {
      cancelled = true;
    };
  }, [metrics, selectedNode, selectedTaskId]);

  return (
    <main className="screen-shell detail-screen">
      <div className="screen-overlay" />

      <section className="screen-content detail-layout">
        <header className="topbar">
          <div className="topbar-left">
            <Link className="icon-button icon-button-link" to="/" aria-label="Back to dashboard">
              <span />
              <span />
              <span />
            </Link>
            <div className="page-title">
              Node-01 <span className="page-subtitle">(node-id-name)</span>
            </div>
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

        <div className="detail-main">
          <aside className="side-panel">
            <ul className="side-list">
              <li>Node-01 (node-id-name)</li>
              <li>CPU Peak: {Math.round(latest.cpu)}%</li>
              <li>CPU Min: {Math.round(latest.cpu * 0.8)}%</li>
              <li>Status: {taskStatus}</li>
              <li>Memory: {formatMemoryAmount(usedMemoryGb)} / {formatMemoryAmount(totalMemoryGb)}</li>
              <li>Network I/O: {networkText}</li>
              <li>Latest runtime: {executionCardDetails.currentRuntime}</li>
            </ul>
          </aside>

          <section className="detail-content">
            <div className="detail-badges">
              <MetricBadge label="CPU Peak:" value={`${Math.round(latest.cpu)}%`} />
              <MetricBadge label="CPU Min:" value={`${Math.round(latest.cpu * 0.8)}%`} />
              <MetricBadge label="Status:" value={taskStatus} />
              <MetricBadge label="Memory:" value={`${formatMemoryAmount(usedMemoryGb)} / ${formatMemoryAmount(totalMemoryGb)}`} />
              <MetricBadge label="Network I/O" value={networkText} />
              <MetricBadge label="Latest Runtime" value={executionCardDetails.currentRuntime} />
            </div>

            <div className="detail-grid">
              <article className="panel resource-card-wide">
                <div className="card-header">
                  <h3>CPU Resource Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="resource-content">
                  <div className="resource-chart-stack">
                    <MiniChart data={resourceChart} dataKey="value" color="#7ee5ff" height={122} />
                    <div className="resource-meta">Memory: {memoryPercent.toFixed(1)}%</div>
                    <div className="resource-meta">Temperature: {latest.temperature.toFixed(1)} deg</div>
                  </div>
                  <Gauge value={latest.cpu} max={100} unit="%" label="CPU" tone="cyan" size={190} />
                </div>
              </article>

              <article className="panel power-card-wide">
                <div className="card-header">
                  <h3>Temperature Trend</h3>
                  <div className="panel-info">i</div>
                </div>
                <LineChartComponent
                  data={temperatureChart}
                  dataKey="value"
                  color="#ffcd58"
                  yLabelFormatter={(value) => `${Math.round(value)} deg`}
                />
              </article>

              <article className="panel mini-metric-card">
                <div className="card-header">
                  <h3>Temperature</h3>
                  <div className="panel-info">i</div>
                </div>
                <MiniChart data={history.map((entry) => ({ label: entry.label, value: entry.temperature }))} dataKey="value" color="#64d7ff" />
                <div className="mini-card-bottom">
                  <div className="mini-card-meta">
                    <div className="resource-meta">CPU: {latest.cpu.toFixed(1)}%</div>
                    <div className="resource-meta">Memory: {memoryPercent.toFixed(1)}%</div>
                  </div>
                  <Gauge value={latest.temperature} max={100} unit=" deg" label="TEMP" tone="blue" size={160} />
                </div>
              </article>

              <article className="panel mini-metric-card">
                <div className="card-header">
                  <h3>CPU</h3>
                  <div className="panel-info">i</div>
                </div>
                <MiniChart data={cpuChart} dataKey="value" color="#ffcc59" />
                <div className="mini-card-bottom">
                  <div className="mini-card-meta">
                    <div className="resource-meta">Avg runtime: {executionCardDetails.averageRuntime}</div>
                    <div className="resource-meta">Memory: {formatMemoryAmount(usedMemoryGb)}</div>
                  </div>
                  <Gauge value={latest.cpu} unit="%" label="CPU" tone="amber" size={160} />
                </div>
              </article>

              <article className="panel cpu-usage-card">
                <div className="card-header">
                  <h3>CPU Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <LineChartComponent data={cpuChart} dataKey="value" color="#f0ce5b" yLabelFormatter={(value) => `${Math.round(value)}%`} />
              </article>

              <article className="panel disk-card">
                <div className="card-header">
                  <h3>Memory Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="disk-status">Node Status <span>Active</span></div>
                <div className="disk-layout">
                  <div>
                    <div className="disk-value">{formatMemoryAmount(usedMemoryGb)}</div>
                    <div className="disk-label">Used Memory</div>
                    <div className="disk-meta">Available: {formatMemoryAmount(availableMemoryGb)}</div>
                    <div className="disk-meta">Backend memory: {memoryPercent.toFixed(1)}%</div>
                  </div>
                  <Gauge value={memoryPercent} unit="%" label="" tone="blue" size={132} />
                </div>
                <div className="disk-explanation">{memoryExplanation}</div>
              </article>

              <article className="panel switch-card">
                <div className="card-header">
                  <h3>Composite Score</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="composite-score-value">{compositeScoreDetails.scoreText}</div>
                <div className="composite-score-label">
                  {compositeScoreDetails.scoreLabel || "Real-Time Score For"} {selectedNode?.label || "This Node"}
                </div>
                <div className="composite-score-formula">{compositeScoreDetails.formulaText}</div>
                <div className="composite-score-explanation">{compositeScoreDetails.explanation}</div>
                <details className="composite-score-details">
                  <summary>Score logic</summary>
                  <div className="composite-score-note">{compositeScoreDetails.note}</div>
                </details>
              </article>

              <article className="panel workload-card">
                <div className="card-header">
                  <h3>Workload &amp; Execution</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="workload-text">{executionCardDetails.description}</div>
                <div className="workload-list">
                  <div>Current: <span>{executionCardDetails.currentRuntime}</span></div>
                  <div>Average: <span>{executionCardDetails.averageRuntime}</span></div>
                </div>
                <MiniChart data={executionChart} dataKey="value" color="#c7ef99" height={88} />
              </article>

              <article className="panel network-card">
                <div className="card-header">
                  <h3>User Input</h3>
                  <div className="network-rate">{networkText}</div>
                </div>
                <div className="network-node-name">{taskNodeName}</div>
                <div className="network-file">{networkInputText}</div>
                <ul className="network-list">
                  <li>task id: {selectedTaskId || "Not available"}</li>
                  <li>node id: {taskNodeId}</li>
                  <li>execution time: {taskExecutionTime}</li>
                  <li>status: {taskStatus}</li>
                  <li>node name: {taskNodeName}</li>
                </ul>
              </article>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
 
