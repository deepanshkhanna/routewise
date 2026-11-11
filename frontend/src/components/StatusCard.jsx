export default function StatusCard({ label, value, hint }) {
  return (
    <article className="card">
      <p className="card-label">{label}</p>
      <p className="card-value">{value}</p>
      {hint ? <p className="card-hint">{hint}</p> : null}
    </article>
  );
}
