import { memo } from 'react';
import { Handle, Position } from 'reactflow';

function RouterNode({ data }) {
  const down = data?.status === 'down';
  return (
    <div
      style={{
        minWidth: 120,
        padding: '12px 14px',
        borderRadius: 12,
        border: `1px solid ${down ? 'rgba(244,63,94,.55)' : '#52525b'}`,
        background: down ? '#1a1012' : '#1a1a1a',
        boxShadow: '0 8px 24px rgba(0,0,0,.45)',
        color: '#fafafa',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ width: 8, height: 8, background: '#e4e4e7', border: 'none' }}
      />
      <div style={{ fontSize: 13, fontWeight: 600 }}>{data?.label || 'Router'}</div>
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
      <div style={{ marginTop: 6, fontSize: 11, color: down ? '#fda4af' : '#86efac' }}>
        {down ? 'down' : 'up'} · {data?.protocol || 'OSPF'}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ width: 8, height: 8, background: '#e4e4e7', border: 'none' }}
      />
    </div>
  );
}

export default memo(RouterNode);
