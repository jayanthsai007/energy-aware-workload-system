export function formatTimestamp(value, index) {
  if (!value) {
    return `T${index + 1}`;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return `T${index + 1}`;
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatPower(value) {
  return `${(Number(value) || 0).toFixed(1)} W`;
}

export function formatVoltage(value) {
  return `${(Number(value) || 0).toFixed(2)} V`;
}

export function formatTemperature(value) {
  return `${Math.round(Number(value) || 0)}°C`;
}

export function average(values) {
  if (!values.length) {
    return 0;
  }

  return values.reduce((sum, item) => sum + item, 0) / values.length;
}

export function buildHistory(metrics) {
  return [...metrics]
    .slice()
    .reverse()
    .map((entry, index) => ({
      nodeId: entry.node_id || entry.nodeId || "",
      label: formatTimestamp(entry.timestamp, index),
      cpu: Number(entry.cpu) || 0,
      memory: Number(entry.memory) || 0,
      temperature: Number(entry.temperature) || 0,
      power: 68 + (Number(entry.cpu) || 0) * 0.36,
      network: 8 + (Number(entry.memory) || 0) * 0.07,
    }));
}

export function getNodeHistory(metrics, nodeId) {
  return buildHistory(
    (metrics || []).filter((entry) => (entry.node_id || entry.nodeId || "") === nodeId)
  );
}

export function getLatestMetricForNode(metrics, nodeId) {
  const nodeHistory = getNodeHistory(metrics, nodeId);
  return nodeHistory[nodeHistory.length - 1] || {
    nodeId,
    label: "--:--",
    cpu: 0,
    memory: 0,
    temperature: 0,
    power: 0,
    network: 0,
  };
}

export function getNodePalette(index, cpuValue = 0) {
  const palettes = ["#87e6ff", "#ffd164", "#ff7b66", "#ffb677"];
  const gaugeTones = ["cyan", "amber", cpuValue >= 90 ? "red" : "amber", "amber"];

  return {
    line: palettes[index % palettes.length],
    gaugeTone: cpuValue >= 90 ? "red" : gaugeTones[index % gaugeTones.length],
  };
}

export function createNodeCards(nodes, history) {
  const sourceNodes = nodes.length
    ? nodes
    : Array.from({ length: 4 }, (_, index) => ({
        node_id: `placeholder-${index + 1}`,
        status: "ACTIVE",
        cpu_cores: 8,
        memory: 16,
      }));

  return sourceNodes.slice(0, 4).map((node, index) => {
    const nodeHistory = history.filter((entry) => entry.nodeId === node.node_id);
    const latest = nodeHistory[nodeHistory.length - 1] || {
      cpu: 0,
      memory: 0,
      temperature: 0,
      power: 0,
    };
    const cpuValue = Math.min(99, Math.max(0, latest.cpu));
    const temperatureValue = Math.max(0, latest.temperature);
    const powerValue = latest.power;
    const voltageValue = 1.15;
    const palette = getNodePalette(index, cpuValue);

    return {
      node_id: node.node_id,
      label: node.node_name || `Node ${index + 1}`,
      status: node.status || "ACTIVE",
      cpuCores: node.cpu_cores || 0,
      totalMemory: node.total_memory || node.memory || 0,
      totalStorage: node.total_storage || node.storage || 0,
      cpuValue,
      temperatureText: formatTemperature(temperatureValue),
      powerText: formatPower(powerValue),
      voltageText: formatVoltage(voltageValue),
      gaugeTone: palette.gaugeTone,
      tone: palette.line,
      chartData: nodeHistory.map((item, pointIndex) => ({
        label: item.label,
        value: item.cpu,
        pointIndex,
      })),
    };
  });
}

export function createExecutionSummary(executionMetrics) {
  const latest = executionMetrics[0] || {};

  return {
    cpuPeak: Math.round(Number(latest.cpu_peak) || 90),
    cpuMin: Math.round(Math.max(8, (Number(latest.cpu_avg) || 24) - 7)),
    load: ((Number(latest.execution_time) || 1.2) / 10).toFixed(1),
    ramUsed: (Number(latest.memory_avg) || 8.5).toFixed(1),
    networkIo: `${(12 + (Number(latest.memory_peak) || 0) * 0.08).toFixed(0)} KB/s`,
    version: "1.2.2.4V",
    currentRuntime: `${Math.max(1, Math.round((Number(latest.execution_time) || 200) / 60))}h ${Math.round((Number(latest.execution_time) || 200) % 60)}m`,
    averageRuntime: `${Math.max(2, Math.round((average(executionMetrics.map((item) => Number(item.execution_time) || 0)) || 310) / 60))}h 10m`,
  };
}
