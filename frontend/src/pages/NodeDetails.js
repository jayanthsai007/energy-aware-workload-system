import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchNodeBundle } from "../api";
import Gauge from "../components/Gauge";
import LineChartComponent from "../components/LineChart";
import MiniChart from "../components/MiniChart";
import {
  buildHistory,
  createExecutionSummary,
  createNodeCards,
  formatPower,
  formatTemperature,
  formatVoltage,
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

function ToggleRow({ label }) {
  return (
    <div className="toggle-row">
      <span className="toggle-row-icon">o</span>
      <span>{label}</span>
      <span className="switch-pill">ON</span>
    </div>
  );
}

export default function NodeDetails() {
  const { id } = useParams();
  const [nodes, setNodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [executionMetrics, setExecutionMetrics] = useState([]);
  const [error, setError] = useState("");

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
        setError("");
      } catch (loadError) {
        if (!cancelled) {
          setError("Unable to load backend data for the node details screen.");
        }
      }
    }

    loadDetails();
    const intervalId = window.setInterval(loadDetails, 12000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [id]);

  const history = useMemo(() => buildHistory(metrics), [metrics]);
  const summary = useMemo(() => createExecutionSummary(executionMetrics), [executionMetrics]);
  const nodeCards = useMemo(() => createNodeCards(nodes, history), [nodes, history]);
  const selectedNode = nodeCards.find((node) => node.node_id === id) || nodeCards[0];
  const latest = history[history.length - 1] || {
    cpu: 0,
    memory: 0,
    temperature: 0,
    power: 0,
    network: 0,
  };

  const resourceChart = history.map((entry) => ({ label: entry.label, value: entry.cpu }));
  const powerChart = history.map((entry) => ({ label: entry.label, value: entry.power }));
  const cpuChart = history.map((entry) => ({ label: entry.label, value: entry.cpu }));
  const executionChart = history.map((entry, index) => ({
    label: index % 2 === 0 ? "Time" : "",
    value: 2 + entry.cpu / 28,
  }));

  const diskUsage = Math.min(95, Math.max(30, latest.memory * 0.68));
  const networkText = `${latest.network.toFixed(0)} KB/s`;

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
              <li>CPU Peak: {summary.cpuPeak}%</li>
              <li>CPU Min: {summary.cpuMin}%</li>
              <li>Load: {summary.load}</li>
              <li>RAM: {summary.ramUsed} GB / 136 GB</li>
              <li>Network I/O: {networkText}</li>
              <li>{summary.version}</li>
            </ul>
          </aside>

          <section className="detail-content">
            <div className="detail-badges">
              <MetricBadge label="CPU Peak:" value={`${summary.cpuPeak}%`} />
              <MetricBadge label="CPU Min:" value={`${summary.cpuMin}%`} />
              <MetricBadge label="Load:" value={summary.load} />
              <MetricBadge label="RAM:" value={`${summary.ramUsed} GB`} />
              <MetricBadge label="Network I/O" value={networkText} />
              <MetricBadge label="" value={summary.version} />
            </div>

            <div className="detail-grid">
              <article className="panel resource-card-wide">
                <div className="card-header">
                  <h3>Resource Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="resource-content">
                  <div className="resource-chart-stack">
                    <MiniChart data={resourceChart} dataKey="value" color="#7ee5ff" height={122} />
                    <div className="resource-meta">Power: {selectedNode?.powerText || formatPower(latest.power)}</div>
                    <div className="resource-meta">Voltage: {selectedNode?.voltageText || formatVoltage(1.25)}</div>
                  </div>
                  <Gauge value={latest.power} max={130} unit=" W" label="CPU" tone="cyan" size={190} />
                </div>
              </article>

              <article className="panel power-card-wide">
                <div className="card-header">
                  <h3>Power Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <LineChartComponent
                  data={powerChart}
                  dataKey="value"
                  color="#ffcd58"
                  yLabelFormatter={(value) => `${Math.round(value)} W`}
                />
              </article>

              <article className="panel mini-metric-card">
                <div className="card-header">
                  <h3>Temperature</h3>
                  <div className="panel-info">i</div>
                </div>
                <MiniChart data={history.map((entry) => ({ label: entry.label, value: entry.temperature }))} dataKey="value" color="#64d7ff" />
                <div className="mini-card-bottom">
                  <div>
                    <div className="resource-meta">Power: {selectedNode?.powerText || formatPower(latest.power)}</div>
                    <div className="resource-meta">Voltage: {formatVoltage(1.2)}</div>
                  </div>
                  <Gauge value={latest.temperature} max={100} unit=" deg" label="CPU" tone="blue" variant="semi" size={170} />
                </div>
              </article>

              <article className="panel mini-metric-card">
                <div className="card-header">
                  <h3>CPU</h3>
                  <div className="panel-info">i</div>
                </div>
                <MiniChart data={cpuChart} dataKey="value" color="#ffcc59" />
                <div className="mini-card-bottom">
                  <div>
                    <div className="resource-meta">Power: {summary.ramUsed} GB</div>
                    <div className="resource-meta">Voltage: {formatVoltage(1.2)}</div>
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
                  <h3>Disk Usage</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="disk-status">Node Status <span>Active</span></div>
                <div className="disk-layout">
                  <div>
                    <div className="disk-value">{Math.round(diskUsage)}%</div>
                    <div className="disk-label">Disk Usage</div>
                  </div>
                  <Gauge value={diskUsage} unit="%" label="" tone="blue" size={132} />
                </div>
              </article>

              <article className="panel switch-card">
                <div className="card-header">
                  <h3>Control Switches</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="toggle-list">
                  <ToggleRow label="Switch 1" />
                  <ToggleRow label="Switch 2" />
                  <ToggleRow label="Switch 3" />
                </div>
              </article>

              <article className="panel workload-card">
                <div className="card-header">
                  <h3>Workload &amp; Execution</h3>
                  <div className="panel-info">i</div>
                </div>
                <div className="workload-text">Productivity Count</div>
                <div className="workload-list">
                  <div>Current: <span>{summary.currentRuntime}</span></div>
                  <div>Average: <span>{summary.averageRuntime}</span></div>
                </div>
                <MiniChart data={executionChart} dataKey="value" color="#c7ef99" height={88} />
              </article>

              <article className="panel network-card">
                <div className="card-header">
                  <h3>Network I/O</h3>
                  <div className="network-rate">{networkText}</div>
                </div>
                <div className="network-node-name">Node-01</div>
                <div className="network-file">[] data sample.json (batch)</div>
                <ul className="network-list">
                  <li>power: {Math.round(latest.power)}</li>
                  <li>voltage: {formatVoltage(1.25)}</li>
                  <li>temperature: {formatTemperature(latest.temperature)}</li>
                  <li>cpu: {Math.round(latest.cpu)}%</li>
                </ul>
              </article>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
