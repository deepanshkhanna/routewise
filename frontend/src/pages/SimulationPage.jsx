import { useState } from 'react';
import Page from '../components/layout/Page.jsx';
import TopologyCanvas from '../components/topology/TopologyCanvas.jsx';
import { api } from '../services/api.js';

export default function SimulationPage({ network, setNetwork, refresh }) {
  const [log, setLog] = useState([]);
  const [path, setPath] = useState([]);
  const [error, setError] = useState('');

  const refreshPath = async (detail) => {
    const traced = await api.getPaths(detail.id, 'R1', 'R3');
    setPath(traced.protocol_selected_path?.hops || []);
  };

  const act = async (fn, label) => {
    setError('');
    try {
      const result = await fn();
      const detail = await api.getNetwork(network.id);
      setNetwork(detail);
      await refreshPath(detail);
      setLog((prev) => [`${label}: ${result.message}`, ...prev].slice(0, 12));
      refresh?.();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Page
      title="Simulation Lab"
      subtitle="Fail and restore links to demonstrate alternate-path recovery."
    >
      {error ? <div className="banner error">{error}</div> : null}
      <div className="toolbar">
        {(network?.links || []).map((link) => (
          <button
            key={link.id}
            type="button"
            className="btn btn-ghost"
            onClick={() =>
              act(
                () =>
                  link.enabled
                    ? api.disableLink(network.id, link.id)
                    : api.enableLink(network.id, link.id),
                `${link.source_router}-${link.target_router}`,
              )
            }
          >
            {link.enabled ? 'Disable' : 'Restore'} {link.source_router}-{link.target_router}
          </button>
        ))}
      </div>
      <div className="grid-2">
        <div className="card card-pad">
          {network ? <TopologyCanvas network={network} highlightPath={path} /> : null}
        </div>
        <div className="card card-pad">
          <h3 className="card-title">Recovery path R1 → R3</h3>
          <p className="mono" style={{ marginTop: 8 }}>
            {path.length ? path.join(' → ') : 'Trigger a failure to recompute'}
          </p>
          <h3 className="card-title" style={{ marginTop: 18 }}>
            Simulation log
          </h3>
          <ul style={{ margin: '8px 0 0', paddingLeft: 18, color: 'var(--rw-text-muted)' }}>
            {log.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </Page>
  );
}
