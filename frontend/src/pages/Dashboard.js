import { useEffect, useMemo, useState } from "react";
import { fetchDashboardBundle } from "../api";
import DashboardNodePanel from "../components/DashboardNodePanel";
import LineChartComponent from "../components/LineChart";
import StatCard from "../components/StatCard";
import { buildHistory, createNodeCards } from "../utils";

export default function Dashboard() {
  const [nodes, setNodes] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [error, setError] = useState("");

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
        setError("");
      } catch (loadError) {
        if (!cancelled) {
          setError("Unable to connect to backend metrics. Start the backend on http://127.0.0.1:8000.");
        }
      }
    }

    loadDashboard();
    const intervalId = window.setInterval(loadDashboard, 12000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const history = useMemo(() => buildHistory(metrics), [metrics]);
  const nodeCards = useMemo(() => createNodeCards(nodes, history), [nodes, history]);

  const activeNodes = nodes.filter((node) =>
    String(node.status || "").toLowerCase() === "active" ||
    String(node.status || "").toLowerCase() === "online"
  ).length;

  const issueCount = nodeCards.filter((node) => node.cpuValue >= 90).length;
  const chartData = history.length
    ? history.map((entry, index) => ({
        label: index % 2 === 0 ? "Time" : "",
        value: 2.2 + index * 0.05 + entry.cpu / 32,
      }))
    : [{ label: "Time", value: 0 }];

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
            title="Background Problems"
            value={`${issueCount} Issues Detected`}
            accent="danger"
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
                <span>Nodes</span>
                <span className="status-dot" />
              </div>
              <div className="chart-header-actions">
                <span>::</span>
                <span>o</span>
              </div>
            </div>

            <LineChartComponent data={chartData} dataKey="value" color="#96e3ff" />
          </div>

          <aside className="panel info-panel">
            <div className="panel-info">i</div>
            <h3 className="info-panel-title">Input type (file name &amp; meta data)</h3>
            <div className="file-card">
              <div className="file-icon">[]</div>
              <div>
                <div className="file-name">data_sample.json</div>
                <div className="file-subtext">(batch, params...)</div>
              </div>
            </div>
            <div className="info-list">
              <div>Latest backend sync: {history[history.length - 1]?.label || "--:--"}</div>
              <div>CPU signal source: `/metrics`</div>
              <div>Node detail feed: shared backend history</div>
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}
