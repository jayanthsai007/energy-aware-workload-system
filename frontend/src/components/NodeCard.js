import Gauge from "./Gauge";

export default function NodeCard({ node, metrics }) {
  const cpu = metrics.cpu || 0;
  const memory = metrics.memory || 0;
  const temp = metrics.temperature || 0;

  return (
    <div className="node-card">

      <h3>Node {node.node_id.slice(0, 4)}</h3>

      <div className="gauge-container">
        <Gauge value={cpu} />
      </div>

      <div className="node-info">
        <p>Memory: {memory}%</p>
        <p>Temp: {temp}°C</p>
      </div>

    </div>
  );
}