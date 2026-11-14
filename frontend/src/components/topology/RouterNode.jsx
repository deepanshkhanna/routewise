import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { motion } from 'framer-motion';

function RouterNode({ data }) {
  const down = data?.status === 'down';
  const inPath = Boolean(data?.inPath);
  const hopIndex = data?.hopIndex;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{
        opacity: 1,
        scale: inPath ? 1.04 : 1,
      }}
      transition={{ type: 'spring', duration: 0.45, bounce: 0.18 }}
      className={`rw-router-node${down ? ' is-down' : ''}${inPath ? ' is-active-hop' : ''}`}
      style={{
        minWidth: 138,
        padding: '12px 15px',
        borderRadius: 14,
        border: `1.5px solid ${
          down
            ? 'rgba(244,63,94,0.8)'
            : inPath
              ? 'rgba(34,197,94,0.85)'
              : '#52525b'
        }`,
        background: down
          ? 'linear-gradient(160deg, #231115 0%, #140b0d 100%)'
          : inPath
            ? 'linear-gradient(160deg, #12241a 0%, #141716 100%)'
            : 'linear-gradient(160deg, #1d1d20 0%, #141416 100%)',
        boxShadow: down
          ? '0 0 26px rgba(244,63,94,0.35), 0 10px 24px rgba(0,0,0,0.55)'
          : inPath
            ? '0 0 28px rgba(34,197,94,0.32), 0 10px 24px rgba(0,0,0,0.55)'
            : '0 8px 24px rgba(0,0,0,0.45)',
        color: '#fafafa',
        position: 'relative',
      }}
    >
      {inPath && !down ? <span className="rw-node-sonar" aria-hidden="true" /> : null}
      {down ? <span className="rw-node-sonar is-danger" aria-hidden="true" /> : null}

      <Handle
        type="target"
        position={Position.Top}
        style={{
          width: 9,
          height: 9,
          background: down ? '#f43f5e' : inPath ? '#22c55e' : '#e4e4e7',
          border: '2px solid #09090b',
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            className="live-dot"
            style={{
              width: 7,
              height: 7,
              background: down ? '#f43f5e' : '#22c55e',
            }}
          />
          <span style={{ fontSize: 13.5, fontWeight: 700, letterSpacing: '-0.01em' }}>
            {data?.label || 'Router'}
          </span>
        </div>
        {typeof hopIndex === 'number' && hopIndex >= 0 ? (
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '1px 6px',
              borderRadius: 999,
              background: 'rgba(34,197,94,0.2)',
              color: '#86efac',
              border: '1px solid rgba(34,197,94,0.45)',
              fontFamily: 'JetBrains Mono, monospace',
            }}
          >
            HOP {hopIndex + 1}
          </span>
        ) : null}
      </div>

      <div
        style={{
          marginTop: 6,
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: 11,
          color: '#a1a1aa',
        }}
      >
        {data?.loopback || '—'}
      </div>

      <div
        style={{
          marginTop: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 11,
          color: down ? '#fda4af' : inPath ? '#86efac' : '#a1a1aa',
          fontWeight: 500,
        }}
      >
        <span>{down ? 'OFFLINE' : inPath ? 'FORWARDING' : 'STANDBY'}</span>
        <span style={{ opacity: 0.8 }}>{data?.protocol || 'OSPF'}</span>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          width: 9,
          height: 9,
          background: down ? '#f43f5e' : inPath ? '#22c55e' : '#e4e4e7',
          border: '2px solid #09090b',
        }}
      />
    </motion.div>
  );
}

export default memo(RouterNode);
