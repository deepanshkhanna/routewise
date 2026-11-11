/**
 * Static design of the R1–R2–R3 triangle with subnet labels.
 * Live online/offline styling comes from router availability when provided.
 */
export default function TopologyPanel({ routers = [] }) {
  const statusById = Object.fromEntries(
    routers.map((r) => [r.id, r.available ? 'online' : 'offline']),
  );

  const fillFor = (id) =>
    statusById[id] === 'online' ? '#3db8a8' : '#5a6b84';

  return (
    <section className="panel">
      <h3>Network Topology</h3>
      <div className="topology" role="img" aria-label="Triangular topology R1 R2 R3">
        <svg viewBox="0 0 480 280" xmlns="http://www.w3.org/2000/svg">
          {/* Links */}
          <line x1="240" y1="48" x2="110" y2="220" stroke="#4a6285" strokeWidth="2.5" />
          <line x1="240" y1="48" x2="370" y2="220" stroke="#4a6285" strokeWidth="2.5" />
          <line x1="110" y1="220" x2="370" y2="220" stroke="#4a6285" strokeWidth="2.5" />

          {/* Subnet labels */}
          <text className="link-label" x="150" y="120">
            10.0.12.0/30
          </text>
          <text className="link-label" x="290" y="120">
            10.0.13.0/30
          </text>
          <text className="link-label" x="210" y="245">
            10.0.23.0/30
          </text>

          {/* Nodes */}
          <circle cx="240" cy="48" r="22" fill={fillFor('R1')} />
          <circle cx="110" cy="220" r="22" fill={fillFor('R2')} />
          <circle cx="370" cy="220" r="22" fill={fillFor('R3')} />

          <text className="node-label" x="240" y="53" textAnchor="middle">
            R1
          </text>
          <text className="node-label" x="110" y="225" textAnchor="middle">
            R2
          </text>
          <text className="node-label" x="370" y="225" textAnchor="middle">
            R3
          </text>
        </svg>
      </div>
      <p className="placeholder-note" style={{ marginTop: '0.75rem' }}>
        Nodes tint teal when their ContainerLab FRR container is online. Offline
        nodes stay muted — no fabricated live adjacency is shown.
      </p>
    </section>
  );
}
