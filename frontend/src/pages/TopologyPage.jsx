import { useState } from 'react';
import Page from '../components/layout/Page.jsx';
import TopologyCanvas from '../components/topology/TopologyCanvas.jsx';
import { api } from '../services/api.js';

export default function TopologyPage({ network, setNetwork, refresh }) {
  const [selectedLink, setSelectedLink] = useState(null);
  const [msg, setMsg] = useState('');

  const link = network?.links?.find((l) => l.id === selectedLink);

  const toggle = async () => {
    if (!network || !link) return;
    setMsg('');
    try {
      if (link.enabled) await api.disableLink(network.id, link.id);
      else await api.enableLink(network.id, link.id);
      const detail = await api.getNetwork(network.id);
      setNetwork(detail);
      setMsg(link.enabled ? 'Link disabled in simulation.' : 'Link restored.');
      refresh?.();
    } catch (err) {
      setMsg(err.message);
    }
  };

  return (
    <Page
      title="Topology Designer"
      subtitle="Inspect and operate the persisted R1–R2–R3 triangle. Drag, zoom, and select links."
      actions={
        <>
          <button type="button" className="btn btn-ghost" onClick={() => refresh?.()}>
            Refresh
          </button>
          <button type="button" className="btn btn-primary" disabled={!link} onClick={toggle}>
            {link?.enabled === false ? 'Restore link' : 'Disable selected link'}
          </button>
        </>
      }
    >
      {msg ? <div className="banner">{msg}</div> : null}
      <div className="grid-2">
        <div className="card card-pad">
          {network ? (
            <TopologyCanvas network={network} onSelectLink={setSelectedLink} />
          ) : (
            <div className="skeleton" style={{ height: 360 }} />
          )}
        </div>
        <div className="card card-pad">
          <h3 className="card-title">Inspector</h3>
          <p className="card-sub">Select a link on the canvas</p>
          {link ? (
            <table className="table" style={{ marginTop: 12 }}>
              <tbody>
                <tr>
                  <th>Endpoints</th>
                  <td className="mono">
                    {link.source_router} ↔ {link.target_router}
                  </td>
                </tr>
                <tr>
                  <th>Subnet</th>
                  <td className="mono">{link.subnet}</td>
                </tr>
                <tr>
                  <th>Cost</th>
                  <td>{link.cost}</td>
                </tr>
                <tr>
                  <th>Latency</th>
                  <td>{link.latency_ms} ms</td>
                </tr>
                <tr>
                  <th>Loss</th>
                  <td>{link.packet_loss_pct}%</td>
                </tr>
                <tr>
                  <th>Status</th>
                  <td>
                    <span className={`badge ${link.enabled ? 'ok' : 'err'}`}>
                      <span className="dot" />
                      {link.enabled ? 'up' : 'down'}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          ) : (
            <p className="card-sub" style={{ marginTop: 16 }}>
              No link selected.
            </p>
          )}
          <h3 className="card-title" style={{ marginTop: 20 }}>
            Routers
          </h3>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Loopback</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(network?.routers || []).map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.name}</td>
                  <td className="mono">{r.loopback}</td>
                  <td>
                    <span className={`badge ${r.status === 'up' ? 'ok' : 'err'}`}>
                      <span className="dot" />
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Page>
  );
}
