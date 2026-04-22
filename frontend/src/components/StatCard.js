export default function StatCard({ icon, title, value, subtitle, accent = "default" }) {
  return (
    <div className={`stat-card panel stat-card-${accent}`}>
      <div className="panel-dot" />
      <div className="panel-info">i</div>

      <div className="stat-card-heading">
        <span className="stat-card-icon">{icon}</span>
        <span>{title}</span>
      </div>

      <div className="stat-card-value">{value}</div>
      {subtitle ? <div className="stat-card-subtitle">{subtitle}</div> : null}
    </div>
  );
}
