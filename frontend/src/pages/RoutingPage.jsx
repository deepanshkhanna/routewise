import { useEffect, useState } from 'react';
import Page from '../components/layout/Page.jsx';
import { api } from '../services/api.js';

export default function RoutingPage({ network }) {
  const [routes, setRoutes] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [protoMsg, setProtoMsg] = useState('');
  const [form, setForm] = useState({
    router_name: 'R1',
    destination: '192.168.3.3/32',
    next_hop: '10.0.13.2',
    metric: 1,
  });
  const [msg, setMsg] = useState('');

  const load = async () => {
    if (!network) return;
    setRoutes(await api.getStaticRoutes(network.id));
  };

  const loadProtocols = async () => {
    try {
      const data = await api.getProtocolReadiness();
      setProtocols(data.protocols || []);
      setProtoMsg(data.message || '');
    } catch (err) {
      setProtoMsg(err.message || 'Protocol status unavailable');
      setProtocols([
        {
          id: 'static',
          name: 'Static',
          badge: 'ok',
          label: 'Operational (DB)',
          detail: '',
        },
        {
          id: 'rip',
          name: 'RIP v2',
          badge: 'warn',
          label: 'Status unreachable',
          detail: '',
        },
        {
          id: 'ospf',
          name: 'OSPF',
          badge: 'warn',
          label: 'Status unreachable',
          detail: '',
        },
        {
          id: 'bgp',
          name: 'BGP',
          badge: 'muted',
          label: 'Future extension',
          detail: '',
        },
      ]);
    }
  };

  useEffect(() => {
    load().catch((err) => setMsg(err.message));
    loadProtocols();
    const timer = setInterval(loadProtocols, 15000);
    return () => clearInterval(timer);
  }, [network?.id]);

  const add = async () => {
    setMsg('');
    try {
      await api.addStaticRoute(network.id, {
        ...form,
        metric: Number(form.metric) || 1,
      });
      setMsg('Static route stored in software_simulation DB.');
      await load();
    } catch (err) {
      setMsg(err.message);
    }
  };

  const badgeClass = (badge) => {
    if (badge === 'ok') return 'badge ok';
    if (badge === 'warn') return 'badge warn';
    if (badge === 'err') return 'badge err';
    return 'badge';
  };

  return (
    <Page
      title="Routing Manager"
      subtitle="Static routes persist in SQLite. RIP v2 and OSPF status are read from the live FRR lab when deployed."
    >
      {!network ? <div className="banner">Loading network…</div> : null}
      {msg ? <div className="banner">{msg}</div> : null}
      {network && routes.length === 0 ? (
        <div className="banner">
          No static routes yet — add one below. Seeded OSPF triangle remains active for path
          simulation.
        </div>
      ) : null}
      <div className="grid-2">
        <section className="card card-pad">
          <h3 className="card-title">Add static route</h3>
          <div className="toolbar" style={{ marginTop: 12 }}>
            <label className="field">
              Router
              <select
                className="select"
                value={form.router_name}
                onChange={(e) => setForm({ ...form, router_name: e.target.value })}
              >
                {(network?.routers || []).map((r) => (
                  <option key={r.id} value={r.name}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              Destination
              <input
                className="input"
                value={form.destination}
                onChange={(e) => setForm({ ...form, destination: e.target.value })}
              />
            </label>
            <label className="field">
              Next hop
              <input
                className="input"
                value={form.next_hop}
                onChange={(e) => setForm({ ...form, next_hop: e.target.value })}
              />
            </label>
            <button type="button" className="btn btn-primary" onClick={add}>
              Save route
            </button>
          </div>
          <table className="table" style={{ marginTop: 8 }}>
            <thead>
              <tr>
                <th>Router</th>
                <th>Destination</th>
                <th>Next hop</th>
                <th>Metric</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((route) => (
                <tr key={route.id}>
                  <td className="mono">{route.router_name}</td>
                  <td className="mono">{route.destination}</td>
                  <td className="mono">{route.next_hop}</td>
                  <td>{route.metric}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="card card-pad">
          <h3 className="card-title">Protocol readiness</h3>
          <table className="table" style={{ marginTop: 12 }}>
            <tbody>
              {protocols.map((p) => (
                <tr key={p.id}>
                  <th>{p.name}</th>
                  <td>
                    <span className={badgeClass(p.badge)}>
                      <span className="dot" /> {p.label}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="card-sub" style={{ marginTop: 12 }}>
            {protoMsg ||
              'RIP v2 and OSPF are probed from FRR when the ContainerLab topology is deployed.'}
          </p>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ marginTop: 8 }}
            onClick={loadProtocols}
          >
            Refresh protocols
          </button>
        </section>
      </div>
    </Page>
  );
}
