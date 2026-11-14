import { Activity, Link2, Router, ShieldAlert } from 'lucide-react';
import Page from '../components/layout/Page.jsx';
import MetricCard from '../components/ui/MetricCard.jsx';
import TrafficAreaChart from '../components/charts/TrafficAreaChart.jsx';
import TopologyCanvas from '../components/topology/TopologyCanvas.jsx';

export default function Dashboard({ overview, network, lab, loading, error }) {
  return (
    <Page
      title="Network intelligence"
      subtitle="Operational overview across the simulated triangle and optional FRR lab."
    >
      {error ? <div className="banner error">{error}</div> : null}
      {overview?.message ? <div className="banner">{overview.message}</div> : null}

      <div className="grid-kpi">
        <MetricCard
          index={0}
          label="Total routers"
          value={loading ? '—' : overview?.total_routers ?? 0}
          trend={lab?.running ? 'FRR lab detected' : 'Simulation plane'}
          trendDir={lab?.running ? 'up' : 'down'}
          icon={Router}
        />
        <MetricCard
          index={1}
          label="Active links"
          value={loading ? '—' : overview?.active_links ?? 0}
          hint="Enabled and up"
          icon={Link2}
        />
        <MetricCard
          index={2}
          label="Failed links"
          value={loading ? '—' : overview?.failed_links ?? 0}
          trend={overview?.failed_links ? 'Attention required' : 'Healthy fabric'}
          trendDir={overview?.failed_links ? 'down' : 'up'}
          icon={ShieldAlert}
        />
        <MetricCard
          index={3}
          label="Network health"
          value={overview?.failed_links ? 'Degraded' : 'Stable'}
          hint={overview?.data_source || 'software_simulation'}
          icon={Activity}
        />
      </div>

      <div className="grid-2">
        <section className="card card-pad">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <h3 className="card-title">Path quality overview</h3>
              <p className="card-sub">Latency vs loss (illustrative series)</p>
            </div>
            <div className="badge">
              <span className="live-dot" /> Live UI
            </div>
          </div>
          <TrafficAreaChart />
        </section>

        <section className="card card-pad">
          <h3 className="card-title">Recent incidents</h3>
          <p className="card-sub">Event stream from the control plane</p>
          <table className="table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Event</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {(overview?.recent_events || []).slice(0, 6).map((event) => (
                <tr key={event.id}>
                  <td>
                    <span
                      className={`badge ${
                        event.severity === 'critical' || event.severity === 'warning' ? 'warn' : 'ok'
                      }`}
                    >
                      <span className="dot" />
                      {event.severity}
                    </span>
                  </td>
                  <td>{event.description}</td>
                  <td className="mono">{event.data_source}</td>
                </tr>
              ))}
              {!overview?.recent_events?.length ? (
                <tr>
                  <td colSpan={3} className="card-sub">
                    No events yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </section>
      </div>

      <section className="card card-pad" style={{ marginTop: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="card-title">Topology snapshot</h3>
            <p className="card-sub">Live packet path preview — open Simulation Lab for interactive failover</p>
          </div>
          <span className="badge ok">
            <span className="live-dot" /> Active Flow R1 → R3
          </span>
        </div>
        <div style={{ marginTop: 12 }}>
          {network ? (
            <TopologyCanvas
              network={network}
              highlightPath={
                network.links?.some(
                  (l) =>
                    ((l.source_router === 'R1' && l.target_router === 'R3') ||
                      (l.source_router === 'R3' && l.target_router === 'R1')) &&
                    (!l.enabled || l.status !== 'up'),
                )
                  ? ['R1', 'R2', 'R3']
                  : ['R1', 'R3']
              }
            />
          ) : (
            <div className="skeleton" style={{ height: 280 }} />
          )}
        </div>
      </section>
    </Page>
  );
}
