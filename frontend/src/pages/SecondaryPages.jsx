import { useEffect, useState } from 'react';
import Page from '../components/layout/Page.jsx';
import TrafficAreaChart from '../components/charts/TrafficAreaChart.jsx';
import { api } from '../services/api.js';

export function AnalyticsPage() {
  return (
    <Page title="Analytics" subtitle="Performance trends for demos — labeled where data is illustrative.">
      <div className="grid-2">
        <section className="card card-pad">
          <h3 className="card-title">Latency & loss</h3>
          <TrafficAreaChart />
        </section>
        <section className="card card-pad">
          <h3 className="card-title">Availability</h3>
          <p className="metric-value">99.2%</p>
          <p className="card-sub">Synthetic availability for UI demonstration</p>
          <div style={{ marginTop: 18, display: 'grid', gap: 10 }}>
            {[
              ['R1 reachability', 100],
              ['R2 reachability', 100],
              ['R3 reachability', 98],
            ].map(([label, value]) => (
              <div key={label}>
                <div className="metric-label">
                  <span>{label}</span>
                  <span>{value}%</span>
                </div>
                <div style={{ height: 8, borderRadius: 999, background: '#1f1f22', marginTop: 6 }}>
                  <div
                    style={{
                      width: `${value}%`,
                      height: '100%',
                      borderRadius: 999,
                      background: '#fafafa',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Page>
  );
}

export function EventsPage({ network }) {
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!network) return;
    api
      .getEvents(network.id)
      .then(setEvents)
      .catch((err) => setError(err.message));
  }, [network?.id]);

  return (
    <Page title="Events & Alerts" subtitle="Simulation and topology change history.">
      {error ? <div className="banner error">{error}</div> : null}
      <section className="card card-pad">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Severity</th>
              <th>Category</th>
              <th>Description</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id}>
                <td className="mono">{event.id}</td>
                <td>
                  <span
                    className={`badge ${
                      event.severity === 'info' ? 'ok' : event.severity === 'warning' ? 'warn' : 'err'
                    }`}
                  >
                    <span className="dot" />
                    {event.severity}
                  </span>
                </td>
                <td>{event.category}</td>
                <td>{event.description}</td>
                <td className="mono">{event.data_source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </Page>
  );
}

export function ReportsPage({ network, overview }) {
  const report = {
    network: network?.name,
    routers: overview?.total_routers,
    active_links: overview?.active_links,
    failed_links: overview?.failed_links,
    generated_at: new Date().toISOString(),
    data_source: 'software_simulation',
  };

  const download = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'routewise-report.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Page
      title="Reports"
      subtitle="Export a concise performance and topology summary."
      actions={
        <button type="button" className="btn btn-primary" onClick={download}>
          Export JSON
        </button>
      }
    >
      <section className="card card-pad">
        <pre className="mono" style={{ whiteSpace: 'pre-wrap', color: 'var(--rw-text-muted)' }}>
          {JSON.stringify(report, null, 2)}
        </pre>
      </section>
    </Page>
  );
}

export function SettingsPage({ backendOk, lab, refresh }) {
  const [infra, setInfra] = useState(null);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const loadInfra = () => {
    api
      .getInfrastructure()
      .then(setInfra)
      .catch((e) => setErr(e.message));
  };

  useEffect(() => {
    loadInfra();
  }, []);

  const run = async (fn, label) => {
    setBusy(true);
    setErr('');
    setMsg('');
    try {
      const result = await fn();
      setMsg(`${label}: ${result.message || JSON.stringify(result)}`);
      loadInfra();
      refresh?.();
    } catch (e) {
      setErr(e.message || `${label} failed`);
    } finally {
      setBusy(false);
    }
  };

  const real = infra?.real_lab;

  return (
    <Page title="Settings & Lab" subtitle="Infrastructure health and lab lifecycle.">
      {err ? <div className="banner error">{err}</div> : null}
      {msg ? <div className="banner ok">{msg}</div> : null}
      <div className="grid-2">
        <section className="card card-pad">
          <h3 className="card-title">Connectivity</h3>
          <table className="table" style={{ marginTop: 12 }}>
            <tbody>
              <tr>
                <th>Backend API</th>
                <td>
                  <span className={`badge ${backendOk ? 'ok' : 'err'}`}>
                    <span className="dot" />
                    {backendOk ? 'reachable' : 'offline'}
                  </span>
                </td>
              </tr>
              <tr>
                <th>Active mode</th>
                <td className="mono">{infra?.active_mode || '…'}</td>
              </tr>
              <tr>
                <th>Docker</th>
                <td>
                  <span className={`badge ${real?.docker_ok ? 'ok' : 'warn'}`}>
                    <span className="dot" />
                    {real?.docker_ok ? 'ok' : 'down / via WSL pending'}
                  </span>
                </td>
              </tr>
              <tr>
                <th>ContainerLab</th>
                <td>
                  <span className={`badge ${real?.containerlab_ok ? 'ok' : 'warn'}`}>
                    <span className="dot" />
                    {real?.containerlab_ok ? 'ok' : 'missing'}
                  </span>
                </td>
              </tr>
              <tr>
                <th>Lab deployed</th>
                <td>
                  <span className={`badge ${real?.lab_deployed || lab?.running ? 'ok' : 'warn'}`}>
                    <span className="dot" />
                    {real?.lab_deployed || lab?.running ? 'running' : 'not deployed'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <button type="button" className="btn btn-ghost" style={{ marginTop: 12 }} onClick={() => { loadInfra(); refresh?.(); }}>
            Re-check status
          </button>
        </section>
        <section className="card card-pad">
          <h3 className="card-title">Lab management</h3>
          <p className="card-sub" style={{ marginBottom: 12 }}>
            {infra?.message ||
              'SOFTWARE_SIMULATION remains usable when the real lab is unavailable.'}
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy}
              onClick={() => run(api.deployLab, 'Deploy')}
            >
              Deploy lab
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={() => run(api.restartLab, 'Restart')}
            >
              Restart
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={() => run(api.destroyLab, 'Destroy')}
            >
              Destroy lab
            </button>
          </div>
          {real?.routers?.length ? (
            <table className="table" style={{ marginTop: 16 }}>
              <thead>
                <tr>
                  <th>Router</th>
                  <th>Container</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {real.routers.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td className="mono">{r.container}</td>
                    <td className="mono">{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </section>
      </div>
    </Page>
  );
}
