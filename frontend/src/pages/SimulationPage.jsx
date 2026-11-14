import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Play,
  RotateCcw,
  Router as RouterIcon,
  ShieldCheck,
  Sparkles,
  Unplug,
  Zap,
} from 'lucide-react';
import Page from '../components/layout/Page.jsx';
import TopologyCanvas from '../components/topology/TopologyCanvas.jsx';
import { api } from '../services/api.js';

const DEMO_STEPS = [
  {
    id: 1,
    title: '1. Baseline (Normal OSPF)',
    short: 'All 3 links UP · Direct path R1 → R3',
    narration:
      'All links are healthy. OSPF Dijkstra SPF selects the direct link R1 ↔ R3 (10.0.13.0/30) because its cost (15) is lower than the 2-hop transit path via R2 (10 + 10 = 20).',
  },
  {
    id: 2,
    title: '2. Inject Primary Link Failure',
    short: 'Cut R1 ↔ R3 (10.0.13.0/30)',
    narration:
      'Fiber cut simulated on direct link R1 ↔ R3 (eth2). OSPF neighbor adjacency drops, R1 & R3 flood updated Router-LSAs across Area 0, and SPF recomputes.',
  },
  {
    id: 3,
    title: '3. OSPF Convergence & Reroute',
    short: 'Traffic shifts to R1 → R2 → R3',
    narration:
      'Zero-touch recovery complete! Traffic automatically reroutes through transit router R2 (10.0.12.0/30 → 10.0.23.0/30, cost 20, latency 17 ms). End-to-end ping remains 100% reachable.',
  },
  {
    id: 4,
    title: '4. Link Restoration & Preemption',
    short: 'Restore R1 ↔ R3 · Return to optimal path',
    narration:
      'Link R1 ↔ R3 is restored. OSPF Hello/DBD exchange re-establishes FULL adjacency and traffic preemptively shifts back to the lower-cost 1-hop path R1 → R3.',
  },
];

export default function SimulationPage({ network, setNetwork, refresh }) {
  const [source, setSource] = useState('R1');
  const [destination, setDestination] = useState('R3');
  const [pathData, setPathData] = useState(null);
  const [optData, setOptData] = useState(null);
  const [pingResult, setPingResult] = useState(null);
  const [traceResult, setTraceResult] = useState(null);
  const [baselinePath, setBaselinePath] = useState({
    hops: ['R1', 'R3'],
    hop_count: 1,
    total_cost: 15,
    total_latency_ms: 4,
    avg_packet_loss_pct: 0,
  });
  const [activeStep, setActiveStep] = useState(1);
  const [autoPlaying, setAutoPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([]);
  const [error, setError] = useState('');
  const demoAbortRef = useRef(false);

  const appendLog = useCallback((entry, tone = 'info') => {
    const stamp = new Date().toLocaleTimeString();
    setLog((prev) => [{ id: `${Date.now()}-${Math.random()}`, stamp, entry, tone }, ...prev].slice(0, 14));
  }, []);

  const syncTelemetry = useCallback(
    async (netId, src = source, dst = destination) => {
      if (!netId) return null;
      const [detail, paths, opt, pingRes, traceRes] = await Promise.all([
        api.getNetwork(netId),
        api.getPaths(netId, src, dst),
        api.optimizePath(netId, src, dst),
        api.ping(netId, src, dst),
        api.traceroute(netId, src, dst),
      ]);
      setNetwork(detail);
      setPathData(paths);
      setOptData(opt);
      setPingResult(pingRes);
      setTraceResult(traceRes);

      const allUp =
        detail.links?.every((l) => l.enabled && l.status === 'up') &&
        detail.routers?.every((r) => r.status === 'up');
      if (allUp && paths?.protocol_selected_path) {
        setBaselinePath(paths.protocol_selected_path);
      }
      return { detail, paths, opt, pingRes, traceRes };
    },
    [source, destination, setNetwork],
  );

  useEffect(() => {
    if (network?.id) {
      syncTelemetry(network.id, source, destination).catch((err) => setError(err.message));
    }
  }, [network?.id, source, destination, syncTelemetry]);

  const findDirectLink = (detail) =>
    (detail?.links || []).find(
      (l) =>
        (l.source_router === 'R1' && l.target_router === 'R3') ||
        (l.source_router === 'R3' && l.target_router === 'R1'),
    );

  const restoreAll = async (silent = false) => {
    if (!network?.id) return null;
    if (!silent) setBusy(true);
    setError('');
    try {
      const current = await api.getNetwork(network.id);
      for (const link of current.links || []) {
        if (!link.enabled || link.status !== 'up') {
          await api.enableLink(network.id, link.id);
        }
      }
      for (const router of current.routers || []) {
        if (router.status !== 'up') {
          await api.restoreRouter(network.id, router.name);
        }
      }
      const synced = await syncTelemetry(network.id, source, destination);
      setActiveStep(1);
      if (!silent) {
        appendLog('All links and routers restored to healthy baseline (OSPF Area 0 converged).', 'ok');
        refresh?.();
      }
      return synced;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      if (!silent) setBusy(false);
    }
  };

  const runStage = async (stageNumber) => {
    if (!network?.id) return;
    setBusy(true);
    setError('');
    try {
      if (stageNumber === 1) {
        await restoreAll(true);
        setActiveStep(1);
        appendLog('Stage 1: Baseline verified — R1 → R3 direct path active (cost 15, 4 ms).', 'ok');
      } else if (stageNumber === 2 || stageNumber === 3) {
        const current = await api.getNetwork(network.id);
        // Ensure backup links R1-R2 and R2-R3 are up first
        for (const l of current.links || []) {
          const isDirect =
            (l.source_router === 'R1' && l.target_router === 'R3') ||
            (l.source_router === 'R3' && l.target_router === 'R1');
          if (!isDirect && !l.enabled) {
            await api.enableLink(network.id, l.id);
          }
        }
        const direct = findDirectLink(current);
        if (direct && direct.enabled) {
          await api.disableLink(network.id, direct.id);
        }
        const synced = await syncTelemetry(network.id, 'R1', 'R3');
        setActiveStep(stageNumber);
        const newHops = synced?.paths?.protocol_selected_path?.hops?.join(' → ') || 'UNREACHABLE';
        appendLog(
          stageNumber === 2
            ? `Stage 2: Direct link R1 ↔ R3 (10.0.13.0/30) SEVERED! OSPF recalculating SPF tree…`
            : `Stage 3: OSPF converged onto backup path ${newHops} (cost 20, latency 17 ms).`,
          stageNumber === 2 ? 'warn' : 'ok',
        );
      } else if (stageNumber === 4) {
        await restoreAll(true);
        setActiveStep(4);
        appendLog('Stage 4: Link R1 ↔ R3 restored — OSPF preempted back to optimal R1 → R3 path.', 'ok');
      }
      refresh?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const playFullDemo = async () => {
    if (!network?.id || autoPlaying) return;
    demoAbortRef.current = false;
    setAutoPlaying(true);
    setError('');
    try {
      await runStage(1);
      await new Promise((r) => setTimeout(r, 2200));
      if (demoAbortRef.current) return;

      await runStage(2);
      await new Promise((r) => setTimeout(r, 2200));
      if (demoAbortRef.current) return;

      await runStage(3);
      await new Promise((r) => setTimeout(r, 2600));
      if (demoAbortRef.current) return;

      await runStage(4);
    } finally {
      setAutoPlaying(false);
    }
  };

  const toggleLink = async (link) => {
    if (!network?.id) return;
    setBusy(true);
    setError('');
    try {
      if (link.enabled) {
        await api.disableLink(network.id, link.id);
      } else {
        await api.enableLink(network.id, link.id);
      }
      const synced = await syncTelemetry(network.id, source, destination);
      const newHops = synced?.paths?.protocol_selected_path?.hops?.join(' → ') || 'No available route';
      appendLog(
        `Link ${link.source_router} ↔ ${link.target_router} (${link.subnet}) ${
          link.enabled ? 'DISABLED' : 'RESTORED'
        } · Active path: ${newHops}`,
        link.enabled ? 'warn' : 'ok',
      );
      setActiveStep(link.enabled ? 3 : 4);
      refresh?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const toggleRouter = async (router) => {
    if (!network?.id) return;
    setBusy(true);
    setError('');
    try {
      const isUp = router.status === 'up';
      if (isUp) {
        await api.failRouter(network.id, router.name);
      } else {
        await api.restoreRouter(network.id, router.name);
      }
      const synced = await syncTelemetry(network.id, source, destination);
      const newHops = synced?.paths?.protocol_selected_path?.hops?.join(' → ') || 'No available route';
      appendLog(
        `Router ${router.name} (${router.loopback}) ${
          isUp ? 'CRASHED' : 'RESTORED'
        } · Active path: ${newHops}`,
        isUp ? 'warn' : 'ok',
      );
      refresh?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const selectedPath = pathData?.protocol_selected_path;
  const recommendedPath = optData?.recommended_path;
  const highlightHops = selectedPath?.hops || [];
  const hasFailover =
    (network?.links || []).some((l) => !l.enabled || l.status !== 'up') ||
    (network?.routers || []).some((r) => r.status !== 'up');
  const currentStepObj = DEMO_STEPS.find((s) => s.id === activeStep) || DEMO_STEPS[0];

  return (
    <Page
      title="Simulation Lab & Failover Walkthrough"
      subtitle="Interactive OSPF link-failure, Dijkstra SPF convergence, and route-recovery demonstration."
      actions={
        <>
          <button
            type="button"
            className="btn btn-ghost"
            disabled={busy || autoPlaying}
            onClick={() => restoreAll(false)}
          >
            <RotateCcw size={14} /> Reset to Healthy Baseline
          </button>
          <button
            type="button"
            className="btn btn-primary rw-btn-glow"
            disabled={busy || autoPlaying}
            onClick={playFullDemo}
          >
            <Play size={14} />
            {autoPlaying ? 'Running Guided Walkthrough…' : 'Play Guided Professor Demo'}
          </button>
        </>
      }
    >
      {error ? <div className="banner error">{error}</div> : null}

      {/* Guided Professor Walkthrough Stepper */}
      <motion.section
        className="card card-pad rw-sim-hero"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div className="rw-sim-hero-top">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className={`badge ${hasFailover ? 'warn' : 'ok'}`}>
                <span className="dot" />
                {hasFailover ? 'FAILOVER ACTIVE · REROUTED' : 'NORMAL BASELINE · OPTIMAL'}
              </span>
              <span className="badge">
                <Sparkles size={11} /> Interactive Presentation Mode
              </span>
            </div>
            <h3 className="card-title" style={{ marginTop: 8, fontSize: '1.02rem' }}>
              {currentStepObj.title}
            </h3>
          </div>

          <div className="toolbar" style={{ marginBottom: 0 }}>
            <label className="field" style={{ minWidth: 92 }}>
              Source
              <select
                className="select"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                {(network?.routers || []).map((r) => (
                  <option key={r.id} value={r.name}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field" style={{ minWidth: 92 }}>
              Destination
              <select
                className="select"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              >
                {(network?.routers || []).map((r) => (
                  <option key={r.id} value={r.name}>
                    {r.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="rw-stepper-grid">
          {DEMO_STEPS.map((step) => {
            const isCurrent = step.id === activeStep;
            return (
              <button
                key={step.id}
                type="button"
                disabled={busy || autoPlaying}
                onClick={() => runStage(step.id)}
                className={`rw-step-card${isCurrent ? ' is-active' : ''}`}
              >
                <div className="rw-step-num">STEP {step.id}</div>
                <div className="rw-step-title">{step.title.replace(/^\d+\.\s*/, '')}</div>
                <div className="rw-step-sub">{step.short}</div>
              </button>
            );
          })}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentStepObj.id}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
            className="rw-narration-box"
          >
            <Zap size={16} style={{ color: '#22c55e', flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontWeight: 600, color: '#fafafa', fontSize: '0.86rem' }}>
                What is happening right now:
              </div>
              <div style={{ color: 'var(--rw-text-muted)', fontSize: '0.84rem', marginTop: 2 }}>
                {currentStepObj.narration}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </motion.section>

      {/* Live Packet Flow Ribbon */}
      <motion.section
        className="card card-pad"
        style={{ marginTop: 12 }}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28, delay: 0.04 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <h3 className="card-title">Live Packet Forwarding Stream ({source} → {destination})</h3>
            <p className="card-sub">
              Hop-by-hop packet traversal across the currently converged OSPF forwarding table
            </p>
          </div>
          {pingResult ? (
            <span className={`badge ${pingResult.success ? 'ok' : 'err'}`}>
              <span className="dot" />
              {pingResult.success
                ? `ICMP ECHO REPLY · RTT ${pingResult.rtt_ms} ms · 0% Loss`
                : 'ICMP DESTINATION UNREACHABLE'}
            </span>
          ) : null}
        </div>

        {selectedPath ? (
          <div className="rw-packet-Track">
            {selectedPath.hops.map((hop, idx) => {
              const linkInfo = selectedPath.links?.[idx];
              return (
                <div key={hop} style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <motion.div
                    layout
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="rw-hop-node"
                  >
                    <span className="live-dot" />
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{hop}</div>
                      <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--rw-text-muted)' }}>
                        {idx === 0
                          ? 'Ingress'
                          : idx === selectedPath.hops.length - 1
                            ? 'Egress'
                            : `Transit Hop ${idx}`}
                      </div>
                    </div>
                  </motion.div>

                  {linkInfo ? (
                    <div className="rw-hop-pipe">
                      <div className="rw-pipe-line">
                        <span className="rw-packet-orb" />
                        <span className="rw-packet-orb delay-1" />
                      </div>
                      <div className="mono rw-pipe-meta">
                        {linkInfo.subnet} · cost {linkInfo.cost} · {linkInfo.latency_ms}ms
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="banner error" style={{ marginTop: 12, marginBottom: 0 }}>
            No valid route between {source} and {destination} — all candidate paths are currently severed.
          </div>
        )}
      </motion.section>

      {/* Main Split: Topology Canvas + Before/After Comparison */}
      <div className="grid-2" style={{ marginTop: 12 }}>
        <section className="card card-pad">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div>
              <h3 className="card-title">Interactive Topology & Link State</h3>
              <p className="card-sub">Click any link on the canvas or use the fault controls on the right</p>
            </div>
            <span className="badge ok">
              <span className="live-dot" /> Animated Flow
            </span>
          </div>
          {network ? (
            <TopologyCanvas
              network={network}
              highlightPath={highlightHops}
              onSelectLink={(linkId) => {
                const targetLink = network.links?.find((l) => l.id === linkId);
                if (targetLink && !busy) toggleLink(targetLink);
              }}
            />
          ) : (
            <div className="skeleton" style={{ height: 420 }} />
          )}
        </section>

        <div style={{ display: 'grid', gap: 12, alignContent: 'start' }}>
          {/* Before vs After Comparison Card */}
          <section className="card card-pad">
            <h3 className="card-title">Before vs. After Failover Comparison</h3>
            <p className="card-sub">
              Direct proof of how OSPF re-converges when a link state changes
            </p>
            <table className="table" style={{ marginTop: 10 }}>
              <thead>
                <tr>
                  <th>State</th>
                  <th>Selected Path</th>
                  <th>Hops</th>
                  <th>OSPF Cost</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span className="badge">Baseline (Normal)</span>
                  </td>
                  <td className="mono">{baselinePath.hops.join(' → ')}</td>
                  <td>{baselinePath.hop_count}</td>
                  <td className="mono">{baselinePath.total_cost}</td>
                  <td className="mono">{baselinePath.total_latency_ms} ms</td>
                </tr>
                <tr>
                  <td>
                    <span className={`badge ${!selectedPath ? 'err' : hasFailover ? 'warn' : 'ok'}`}>
                      <span className="dot" />
                      {!selectedPath ? 'Partitioned' : hasFailover ? 'Rerouted (Live)' : 'Active (Optimal)'}
                    </span>
                  </td>
                  <td className="mono" style={{ fontWeight: 700, color: '#fafafa' }}>
                    {selectedPath ? selectedPath.hops.join(' → ') : 'UNREACHABLE'}
                  </td>
                  <td>{selectedPath ? selectedPath.hop_count : '—'}</td>
                  <td className="mono">{selectedPath ? selectedPath.total_cost : '—'}</td>
                  <td className="mono">{selectedPath ? `${selectedPath.total_latency_ms} ms` : '—'}</td>
                </tr>
                {recommendedPath ? (
                  <tr>
                    <td>
                      <span className="badge ok">Optimizer Best</span>
                    </td>
                    <td className="mono">{recommendedPath.hops.join(' → ')}</td>
                    <td>{recommendedPath.hop_count}</td>
                    <td className="mono">{recommendedPath.total_cost}</td>
                    <td className="mono">
                      {recommendedPath.total_latency_ms} ms (S={recommendedPath.score})
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </section>

          {/* Direct Link & Router Fault Injection Controls */}
          <section className="card card-pad">
            <h3 className="card-title">Link & Router Fault Injection</h3>
            <p className="card-sub">Cut or restore individual links and routers in real time</p>

            <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
              {(network?.links || []).map((link) => {
                const isUp = link.enabled && link.status === 'up';
                return (
                  <div
                    key={link.id}
                    className={`rw-fault-row${isUp ? '' : ' is-down'}`}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`badge ${isUp ? 'ok' : 'err'}`}>
                          <span className="dot" />
                          {isUp ? 'UP' : 'SEVERED'}
                        </span>
                        <span className="mono" style={{ fontWeight: 600 }}>
                          {link.source_router} ↔ {link.target_router}
                        </span>
                        <span className="mono" style={{ color: 'var(--rw-text-muted)', fontSize: '0.76rem' }}>
                          {link.subnet}
                        </span>
                      </div>
                      <div className="card-sub" style={{ marginTop: 3 }}>
                        OSPF Cost {link.cost} · Latency {link.latency_ms} ms · Loss {link.packet_loss_pct}%
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={busy}
                      className={`btn ${isUp ? 'btn-ghost' : 'btn-primary'}`}
                      onClick={() => toggleLink(link)}
                    >
                      {isUp ? (
                        <>
                          <Unplug size={13} /> Cut Link
                        </>
                      ) : (
                        <>
                          <CheckCircle2 size={13} /> Restore Link
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 10 }}>
              {(network?.routers || []).map((router) => {
                const isUp = router.status === 'up';
                return (
                  <button
                    key={router.id}
                    type="button"
                    disabled={busy}
                    onClick={() => toggleRouter(router)}
                    className={`rw-router-pill${isUp ? '' : ' is-down'}`}
                  >
                    <RouterIcon size={14} />
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 600, fontSize: '0.8rem' }}>{router.name}</div>
                      <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                        {isUp ? 'Online (Click to fail)' : 'Crashed (Restore)'}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Event Timeline */}
          <section className="card card-pad">
            <h3 className="card-title">Live Convergence & Event Feed</h3>
            <div style={{ marginTop: 10, display: 'grid', gap: 6, maxHeight: 190, overflowY: 'auto' }}>
              <AnimatePresence initial={false}>
                {log.length === 0 ? (
                  <p className="card-sub">
                    Click &ldquo;Play Guided Professor Demo&rdquo; or cut a link above to record live convergence events.
                  </p>
                ) : (
                  log.map((item) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      className={`rw-log-item is-${item.tone}`}
                    >
                      <span className="mono rw-log-time">{item.stamp}</span>
                      <span>{item.entry}</span>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </section>
        </div>
      </div>
    </Page>
  );
}
