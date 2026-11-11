import { useEffect, useState } from 'react';
import Page from '../components/layout/Page.jsx';
import { api } from '../services/api.js';

const EMPTY_FORM = {
  name: '',
  action: 'deny',
  protocol: 'icmp',
  source: 'any',
  destination: 'any',
  port: 'any',
  direction: 'forward',
  priority: 100,
  enabled: true,
};

export default function FirewallPage({ network }) {
  const [status, setStatus] = useState(null);
  const [rules, setRules] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [test, setTest] = useState({
    source: '10.0.12.1',
    destination: '10.0.23.2',
    protocol: 'icmp',
    port: 'any',
  });
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    if (!network?.id) return;
    setError('');
    try {
      const [st, list] = await Promise.all([
        api.getFirewallStatus(network.id),
        api.getFirewallRules(network.id),
      ]);
      setStatus(st);
      setRules(list);
    } catch (err) {
      setError(err.message || 'Failed to load firewall');
    }
  };

  useEffect(() => {
    load();
  }, [network?.id]);

  const onCreate = async (e) => {
    e.preventDefault();
    if (!network?.id) return;
    setBusy(true);
    setError('');
    try {
      await api.createFirewallRule(network.id, {
        ...form,
        priority: Number(form.priority) || 100,
      });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err.message || 'Create failed');
    } finally {
      setBusy(false);
    }
  };

  const onTest = async (e) => {
    e.preventDefault();
    if (!network?.id) return;
    setBusy(true);
    setError('');
    try {
      setTestResult(await api.testFirewall(network.id, test));
      await load();
    } catch (err) {
      setError(err.message || 'Test failed');
    } finally {
      setBusy(false);
    }
  };

  if (!network) {
    return (
      <Page title="Firewall & Security" subtitle="Load a network first.">
        <div className="banner warn">No network loaded.</div>
      </Page>
    );
  }

  return (
    <Page
      title="Firewall & Security"
      subtitle="Isolated lab policies only — never touches Windows Defender or host routing."
      actions={
        <span className={`badge ${status?.mode === 'REAL_LAB' ? 'ok' : 'warn'}`}>
          <span className="dot" />
          {status?.mode || '…'} · {status?.engine || '…'}
        </span>
      }
    >
      {error ? <div className="banner error">{error}</div> : null}
      {status ? (
        <div className="banner" style={{ marginBottom: 16 }}>
          {status.message} · {status.enabled_rules}/{status.rule_count} rules enabled
        </div>
      ) : null}

      <div className="grid-2">
        <section className="card card-pad">
          <h3 className="card-title">Add rule</h3>
          <form onSubmit={onCreate} style={{ display: 'grid', gap: 10, marginTop: 12 }}>
            <input
              className="input"
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <div className="grid-2">
              <select
                className="input"
                value={form.action}
                onChange={(e) => setForm({ ...form, action: e.target.value })}
              >
                <option value="allow">allow</option>
                <option value="deny">deny</option>
              </select>
              <select
                className="input"
                value={form.protocol}
                onChange={(e) => setForm({ ...form, protocol: e.target.value })}
              >
                <option value="any">any</option>
                <option value="tcp">tcp</option>
                <option value="udp">udp</option>
                <option value="icmp">icmp</option>
              </select>
            </div>
            <input
              className="input"
              placeholder="Source (IP/CIDR/any)"
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
            />
            <input
              className="input"
              placeholder="Destination (IP/CIDR/any)"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
            />
            <div className="grid-2">
              <input
                className="input"
                placeholder="Port"
                value={form.port}
                onChange={(e) => setForm({ ...form, port: e.target.value })}
              />
              <input
                className="input"
                type="number"
                placeholder="Priority"
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Create rule
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                setError('');
                try {
                  const result = await api.applyFirewall(network.id);
                  setTestResult({
                    allowed: result.ok,
                    message: result.message,
                    matched_rule_id: null,
                    matched_rule_name: null,
                    mode: result.mode,
                  });
                  await load();
                } catch (err) {
                  setError(err.message || 'Apply failed');
                } finally {
                  setBusy(false);
                }
              }}
            >
              Apply to lab (fw1 nftables)
            </button>
          </form>
        </section>

        <section className="card card-pad">
          <h3 className="card-title">Connectivity test</h3>
          <p className="card-sub">First-match evaluation in the active policy engine.</p>
          <form onSubmit={onTest} style={{ display: 'grid', gap: 10, marginTop: 12 }}>
            <input
              className="input"
              value={test.source}
              onChange={(e) => setTest({ ...test, source: e.target.value })}
              placeholder="Source"
            />
            <input
              className="input"
              value={test.destination}
              onChange={(e) => setTest({ ...test, destination: e.target.value })}
              placeholder="Destination"
            />
            <select
              className="input"
              value={test.protocol}
              onChange={(e) => setTest({ ...test, protocol: e.target.value })}
            >
              <option value="icmp">icmp</option>
              <option value="tcp">tcp</option>
              <option value="udp">udp</option>
            </select>
            <button type="submit" className="btn btn-ghost" disabled={busy}>
              Evaluate policy
            </button>
          </form>
          {testResult ? (
            <div className={`banner ${testResult.allowed ? 'ok' : 'error'}`} style={{ marginTop: 12 }}>
              {testResult.allowed ? 'ALLOWED' : 'DENIED'} — {testResult.message}
            </div>
          ) : null}
        </section>
      </div>

      <section className="card card-pad" style={{ marginTop: 16 }}>
        <h3 className="card-title">Rules</h3>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Pri</th>
              <th>Name</th>
              <th>Action</th>
              <th>Proto</th>
              <th>Source</th>
              <th>Dest</th>
              <th>Port</th>
              <th>Hits</th>
              <th>Source</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rules.length === 0 ? (
              <tr>
                <td colSpan={10} className="card-sub">
                  No rules yet — default allow in software lab policy engine.
                </td>
              </tr>
            ) : (
              rules.map((rule) => (
                <tr key={rule.id}>
                  <td className="mono">{rule.priority}</td>
                  <td>{rule.name || `rule-${rule.id}`}</td>
                  <td>
                    <span className={`badge ${rule.action === 'allow' ? 'ok' : 'err'}`}>
                      <span className="dot" />
                      {rule.action}
                    </span>
                  </td>
                  <td className="mono">{rule.protocol}</td>
                  <td className="mono">{rule.source}</td>
                  <td className="mono">{rule.destination}</td>
                  <td className="mono">{rule.port}</td>
                  <td className="mono">{rule.hit_count}</td>
                  <td className="mono">{rule.data_source}</td>
                  <td style={{ display: 'flex', gap: 6 }}>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={async () => {
                        if (rule.enabled) await api.disableFirewallRule(network.id, rule.id);
                        else await api.enableFirewallRule(network.id, rule.id);
                        await load();
                      }}
                    >
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={async () => {
                        await api.deleteFirewallRule(network.id, rule.id);
                        await load();
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </Page>
  );
}
