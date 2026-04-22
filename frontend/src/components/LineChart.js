import {
  Area,
  AreaChart,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) {
    return null;
  }

  const item = payload[0];

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{label}</div>
      <div className="chart-tooltip-value">
        {formatter ? formatter(item.value) : item.value}
      </div>
    </div>
  );
}

export default function LineChartComponent({
  data,
  dataKey = "value",
  color = "#84ddff",
  yLabelFormatter,
}) {
  const gradientId = `chart-gradient-${color.replace("#", "")}`;

  return (
    <div className="main-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.32} />
              <stop offset="75%" stopColor={color} stopOpacity={0.08} />
              <stop offset="100%" stopColor={color} stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "rgba(222,228,255,0.5)", fontSize: 11 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "rgba(222,228,255,0.5)", fontSize: 11 }}
            tickFormatter={yLabelFormatter}
          />
          <Tooltip content={<CustomTooltip formatter={yLabelFormatter} />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2.8}
            fill={`url(#${gradientId})`}
            dot={{ r: 0 }}
            activeDot={{ r: 5, fill: color, stroke: "#dcefff", strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
