import { useEffect, useState } from 'react';
import { api } from '../services/api.js';

export default function ControlPlane({ mode }) {
  const [network, setNetwork] = useState(null);
  const [source, setSource] = useState('R1');
  const [destination, setDestination] = useState('R3');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const overview = await api.getDashboardOverview();
        const id = overview.default_network_id;
        if (!id) {
          throw new Error('No default network');
        }
        const detail = await api.getNetwork(id);
        if (!cancelled) {
          setNetwork(detail);
          setError('');
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const runExplore = async () => {
    if (!network) return;
    setBusy(true);
    setError('');
    try {
      const data = await api.getPaths(network.id, source, destination);
      setResult({ type: 'paths', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const runOptimize = async () => {
    if (!network) return;
    setBusy(true);
    setError('');
    try {
      const data = await api.optimizePath(network.id, source, destination);
      setResult({ type: 'optimize', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const toggleLink = async (linkId, enable) => {
    if (!network) return;
    setBusy(true);
    setError('');
    try {
      if (enable) await api.enableLink(network.id, linkId);
      else await api.disableLink(network.id, linkId);
      const detail = await api.getNetwork(network.id);
      setNetwork(detail);
      const data = await api.getPaths(network.id, source, destination);
      setResult({ type: 'paths', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const runDiag = async (tool) => {
    if (!network) return;
    setBusy(true);
    setError('');
    try {
      const data =
        tool === 'ping'
          ? await api.ping(network.id, source, destination)
          : await api.traceroute(network.id, source, destination);
      setResult({ type: 'diag', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const loadEvents = async () => {
    if (!network) return;
    setBusy(true);
    setError('');
    try {
      const data = await api.getEvents(network.id);
      setResult({ type: 'events', data });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const title =
    mode === 'paths'
      ? 'Path Explorer'
      : mode === 'optimize'
        ? 'Optimization'
        : mode === 'events'
          ? 'Events'
          : 'Simulation Lab';

  return (
    <div>
      <h2 className="page-title">{title}</h2>
      <p className="page-subtitle">
        Software-simulation control plane over the persisted R1–R2–R3 triangle.
        Results are labeled software_simulation until ContainerLab/FRR is online.
      </p>

      {error ? <div className="banner error">{error}</div> : null}
      {!network ? <div className="banner">Loading network…</div> : null}

      {network ? (
        <>
          <div className="panel" style={{ marginBottom: '0.9rem' }}>
            <h3>Network {network.name}</h3>
            <p className="placeholder-note">
              Routers: {network.routers.map((r) => r.name).join(', ')} · Links:{' '}
              {network.links.length}
            </p>
            {(mode === 'paths' || mode === 'optimize' || mode === 'simulate') && (
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '0.8rem' }}>
                <label>
                  Source{' '}
                  <select value={source} onChange={(e) => setSource(e.target.value)}>
                    {network.routers.map((r) => (
                      <option key={r.id} value={r.name}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Destination{' '}
                  <select value={destination} onChange={(e) => setDestination(e.target.value)}>
                    {network.routers.map((r) => (
                      <option key={r.id} value={r.name}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </label>
                {mode === 'paths' ? (
                  <>
                    <button type="button" className="nav-item active" disabled={busy} onClick={runExplore}>
                      Explore paths
                    </button>
                    <button type="button" className="nav-item" disabled={busy} onClick={() => runDiag('ping')}>
                      Ping
                    </button>
                    <button
                      type="button"
                      className="nav-item"
                      disabled={busy}
                      onClick={() => runDiag('traceroute')}
                    >
                      Traceroute
                    </button>
                  </>
                ) : null}
                {mode === 'optimize' ? (
                  <button type="button" className="nav-item active" disabled={busy} onClick={runOptimize}>
                    Recommend path
                  </button>
                ) : null}
              </div>
            )}
          </div>

          {mode === 'simulate' ? (
            <div className="panel" style={{ marginBottom: '0.9rem' }}>
              <h3>Links</h3>
              <div className="table-wrap">
                <table className="data">
                  <thead>
                    <tr>
                      <th>Link</th>
                      <th>Subnet</th>
                      <th>Cost</th>
                      <th>Latency</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {network.links.map((link) => (
                      <tr key={link.id}>
                        <td className="mono">
                          {link.source_router}-{link.target_router}
                        </td>
                        <td className="mono">{link.subnet}</td>
                        <td>{link.cost}</td>
                        <td>{link.latency_ms} ms</td>
                        <td>
                          <span className={`status-chip ${link.enabled ? 'online' : 'offline'}`}>
                            {link.enabled ? 'up' : 'down'}
                          </span>
                        </td>
                        <td>
                          {link.enabled ? (
                            <button type="button" className="nav-item" disabled={busy} onClick={() => toggleLink(link.id, false)}>
                              Disable
                            </button>
                          ) : (
                            <button type="button" className="nav-item" disabled={busy} onClick={() => toggleLink(link.id, true)}>
                              Restore
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {mode === 'events' ? (
            <button type="button" className="nav-item active" disabled={busy} onClick={loadEvents}>
              Refresh events
            </button>
          ) : null}

          {result ? (
            <div className="panel" style={{ marginTop: '0.9rem' }}>
              <h3>Result</h3>
              <pre className="mono" style={{ whiteSpace: 'pre-wrap', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
