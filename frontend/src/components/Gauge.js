const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function polarToCartesian(cx, cy, radius, angleInDegrees) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;

  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians),
  };
}

function describeArc(cx, cy, radius, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

export default function Gauge({
  value = 0,
  max = 100,
  unit = "%",
  label = "CPU",
  tone = "cyan",
  variant = "full",
  size = 170,
}) {
  const safeValue = clamp(Number(value) || 0, 0, max);
  const progress = safeValue / max;

  const tones = {
    cyan: {
      stroke: "#7fe6ff",
      track: "rgba(70, 108, 164, 0.28)",
    },
    amber: {
      stroke: "#ffd160",
      track: "rgba(116, 92, 39, 0.34)",
    },
    red: {
      stroke: "#ff7a66",
      track: "rgba(127, 61, 62, 0.3)",
    },
    blue: {
      stroke: "#5ec7ff",
      track: "rgba(47, 87, 148, 0.3)",
    },
  };

  const palette = tones[tone] || tones.cyan;

  if (variant === "semi") {
    const path = describeArc(100, 100, 70, 180, 360);
    const arcLength = Math.PI * 70;
    const dashOffset = arcLength * (1 - progress);

    return (
      <div className="gauge gauge-semi" style={{ width: size }}>
        <svg viewBox="0 0 200 128" role="img" aria-label={`${label} ${safeValue}${unit}`}>
          <path className="gauge-track" d={path} pathLength={arcLength} />
          <path
            d={path}
            pathLength={arcLength}
            stroke={palette.stroke}
            strokeDasharray={arcLength}
            strokeDashoffset={dashOffset}
            className="gauge-progress"
          />
        </svg>
        <div className="gauge-center gauge-center-semi">
          <div className="gauge-value">
            {Math.round(safeValue)}
            <span>{unit}</span>
          </div>
          <div className="gauge-label">{label}</div>
        </div>
      </div>
    );
  }

  const radius = 76;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <div
      className="gauge gauge-full"
      style={{
        width: size,
        height: size,
        "--gauge-stroke": palette.stroke,
        "--gauge-track": palette.track,
      }}
    >
      <svg viewBox="0 0 200 200" role="img" aria-label={`${label} ${safeValue}${unit}`}>
        <circle className="gauge-ring-shadow" cx="100" cy="100" r={radius} />
        <circle className="gauge-ring-track" cx="100" cy="100" r={radius} />
        <circle
          className="gauge-ring-progress"
          cx="100"
          cy="100"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div className="gauge-center">
        <div className="gauge-value">
          {Math.round(safeValue)}
          <span>{unit}</span>
        </div>
        <div className="gauge-label">{label}</div>
      </div>
    </div>
  );
}
