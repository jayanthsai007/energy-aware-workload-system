import { Link } from "react-router-dom";
import Gauge from "./Gauge";
import MiniChart from "./MiniChart";

export default function DashboardNodePanel({
  node,
  chartData,
  cpuValue,
  temperature,
  power,
  voltage,
  tone,
}) {
  return (
    <Link className="node-card panel" to={`/node/${node.node_id}`}>
      <div className="panel-dot" />
      <div className="panel-info">i</div>

      <h3 className="node-card-title">{node.label}</h3>

      <div className="node-card-body">
        <div className="node-card-chart">
          <MiniChart data={chartData} dataKey="value" color={tone} height={88} />

          <div className="node-card-metrics">
            <div className="node-card-section">Temperature</div>
            <div className="node-card-chart-reading">{temperature}</div>
          </div>
        </div>

        <div className="node-card-gauge">
          <Gauge value={cpuValue} unit="%" label="CPU" tone={node.gaugeTone} size={138} />
          <div className="node-card-metrics node-card-gauge-metrics">
            <div className="node-card-section">CPU Metrics</div>
            <div className="node-card-meta">Power: {power}</div>
            <div className="node-card-meta">Voltage: {voltage}</div>
          </div>
        </div>
      </div>
    </Link>
  );
}
