import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Page from '../components/layout/Page.jsx';
import TopologyCanvas from '../components/topology/TopologyCanvas.jsx';
import { api } from '../services/api.js';

function PathControls({ network, source, setSource, destination, setDestination, onRun, label }) {
  return (
    <div className="toolbar">
      <label className="field">
        Source
        <select className="select" value={source} onChange={(e) => setSource(e.target.value)}>
          {(network?.routers || []).map((r) => (
            <option key={r.id} value={r.name}>
              {r.name}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        Destination
        <select className="select" value={destination} onChange={(e) => setDestination(e.target.value)}>
          {(network?.routers || []).map((r) => (
            <option key={r.id} value={r.name}>
              {r.name}
            </option>
          ))}
        </select>
      </label>
      <button type="button" className="btn btn-primary" onClick={onRun}>
        {label}
      </button>
    </div>
  );
}

export function PathExplorerPage({ network }) {
  const [source, setSource] = useState('R1');
  const [destination, setDestination] = useState('R3');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const run = useCallback(async () => {
    if (!network?.id) return;
    setError('');
    try {
      const data = await api.getPaths(network.id, source, destination);
      setResult(data);
    } catch (err) {
      setError(err.message);
    }
  }, [network?.id, source, destination]);

  useEffect(() => {
    run();
  }, [run]);

  const highlight = result?.protocol_selected_path?.hops || [];

  return (
    <Page title="Path Explorer" subtitle="Trace protocol-selected and candidate paths across the fabric.">
      {!network ? <div className="banner">Loading topology from backend…</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      <PathControls
        network={network}
        source={source}
        setSource={setSource}
        destination={destination}
        setDestination={setDestination}
        onRun={run}
        label="Trace path"
      />
      <div className="grid-2">
        <div className="card card-pad">
          {network ? <TopologyCanvas network={network} highlightPath={highlight} /> : null}
        </div>
        <div className="card card-pad">
          <h3 className="card-title">Hop journey</h3>
          <p className="card-sub">{result?.message || 'Run a trace to populate hops.'}</p>
          {result?.protocol_selected_path ? (
            <motion.div
              key={result.protocol_selected_path.hops.join('-')}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ marginTop: 12 }}
            >
              <div className="badge ok" style={{ marginBottom: 10 }}>
                <span className="dot" /> Protocol-selected (Lowest OSPF Cost)
              </div>
              <p className="mono" style={{ fontSize: '1.05rem', fontWeight: 600 }}>
                {result.protocol_selected_path.hops.join(' → ')}
              </p>
              <p className="card-sub">
                cost {result.protocol_selected_path.total_cost} · latency{' '}
                {result.protocol_selected_path.total_latency_ms} ms · loss{' '}
                {result.protocol_selected_path.avg_packet_loss_pct}%
              </p>
            </motion.div>
          ) : null}
          <h3 className="card-title" style={{ marginTop: 18 }}>
            All Simple Candidate Paths
          </h3>
          <table className="table">
            <thead>
              <tr>
                <th>Path</th>
                <th>Hops</th>
                <th>OSPF Cost</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {(result?.candidate_paths || []).map((path) => (
                <tr key={path.hops.join('-')}>
                  <td className="mono">{path.hops.join(' → ')}</td>
                  <td>{path.hop_count}</td>
                  <td className="mono">{path.total_cost}</td>
                  <td className="mono">{path.total_latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Page>
  );
}

export function OptimizationPage({ network }) {
  const [source, setSource] = useState('R1');
  const [destination, setDestination] = useState('R3');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const run = useCallback(async () => {
    if (!network?.id) return;
    setError('');
    try {
      setResult(await api.optimizePath(network.id, source, destination));
    } catch (err) {
      setError(err.message);
    }
  }, [network?.id, source, destination]);

  useEffect(() => {
    run();
  }, [run]);

  return (
    <Page
      title="Optimization"
      subtitle="Multi-metric recommendation engine (S = 0.35L + 0.25P + 0.20H + 0.20C) — distinct from OSPF cost."
    >
      {!network ? <div className="banner">Loading topology from backend…</div> : null}
      {error ? <div className="banner error">{error}</div> : null}
      <PathControls
        network={network}
        source={source}
        setSource={setSource}
        destination={destination}
        setDestination={setDestination}
        onRun={run}
        label="Recommend path"
      />
      <div className="grid-2">
        <div className="card card-pad">
          <h3 className="card-title">Recommendation</h3>
          {result?.recommended_path ? (
            <motion.div
              key={result.recommended_path.hops.join('-')}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <p className="metric-value" style={{ fontSize: '1.35rem' }}>
                {result.recommended_path.hops.join(' → ')}
              </p>
              <p className="metric-trend up">Score {result.recommended_path.score} (lower is better)</p>
              <p className="card-sub" style={{ marginTop: 10 }}>
                {result.explanation}
              </p>
              <table className="table" style={{ marginTop: 12 }}>
                <tbody>
                  {Object.entries(result.recommended_path.score_breakdown || {}).map(([k, v]) => (
                    <tr key={k}>
                      <th>{k}</th>
                      <td className="mono">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          ) : (
            <p className="card-sub">Run optimization to compare candidates.</p>
          )}
        </div>
        <div className="card card-pad">
          <h3 className="card-title">Protocol vs recommended</h3>
          <p className="card-sub">Keep these concepts distinct.</p>
          <table className="table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Type</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Protocol-selected (OSPF)</td>
                <td className="mono">
                  {result?.protocol_selected_path?.hops?.join(' → ') || '—'}
                </td>
              </tr>
              <tr>
                <td>Optimizer Recommended</td>
                <td className="mono">{result?.recommended_path?.hops?.join(' → ') || '—'}</td>
              </tr>
            </tbody>
          </table>
          <div style={{ marginTop: 12 }}>
            {network ? (
              <TopologyCanvas
                network={network}
                highlightPath={result?.recommended_path?.hops || []}
              />
            ) : null}
          </div>
        </div>
      </div>
    </Page>
  );
}
