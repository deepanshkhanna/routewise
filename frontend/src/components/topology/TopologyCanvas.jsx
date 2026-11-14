import { useEffect, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import RouterNode from './RouterNode.jsx';

const nodeTypes = { router: RouterNode };

function layoutNodes(routers, highlightPath = []) {
  const positions = {
    R1: { x: 280, y: 36 },
    R2: { x: 75, y: 275 },
    R3: { x: 485, y: 275 },
  };
  return (routers || []).map((router, index) => {
    const hopIndex = highlightPath.indexOf(router.name);
    return {
      id: String(router.name),
      type: 'router',
      position: positions[router.name] || { x: 120 + index * 160, y: 160 },
      data: {
        label: router.name,
        loopback: router.loopback,
        status: router.status,
        protocol: router.protocol,
        inPath: hopIndex !== -1,
        hopIndex: hopIndex !== -1 ? hopIndex : null,
      },
      draggable: true,
    };
  });
}

function layoutEdges(links, highlightPath = []) {
  const directedSet = new Set();
  const undirectedSet = new Set();
  for (let i = 0; i < highlightPath.length - 1; i += 1) {
    directedSet.add(`${highlightPath[i]}->${highlightPath[i + 1]}`);
    undirectedSet.add(`${highlightPath[i]}-${highlightPath[i + 1]}`);
    undirectedSet.add(`${highlightPath[i + 1]}-${highlightPath[i]}`);
  }
  return (links || []).map((link) => {
    const key = `${link.source_router}-${link.target_router}`;
    const active = link.enabled && link.status === 'up';
    const highlighted = active && undirectedSet.has(key);
    const reverseFlow =
      highlighted && directedSet.has(`${link.target_router}->${link.source_router}`);

    const source = reverseFlow ? String(link.target_router) : String(link.source_router);
    const target = reverseFlow ? String(link.source_router) : String(link.target_router);

    const statusTag = !active
      ? `✕ SEVERED · ${link.subnet}`
      : highlighted
        ? `⚡ ACTIVE · ${link.subnet} (cost ${link.cost}, ${link.latency_ms}ms)`
        : `${link.subnet} · cost ${link.cost}`;

    return {
      id: `e-${link.id}`,
      source,
      target,
      label: statusTag,
      animated: Boolean(highlighted),
      className: !active
        ? 'rw-edge-severed'
        : highlighted
          ? 'rw-edge-active-flow'
          : 'rw-edge-standby',
      style: {
        stroke: !active ? '#f43f5e' : highlighted ? '#22c55e' : '#52525b',
        strokeWidth: highlighted ? 3.5 : !active ? 2.5 : 2,
        strokeDasharray: !active ? '7 5' : highlighted ? '10 6' : undefined,
        filter: highlighted
          ? 'drop-shadow(0 0 8px rgba(34, 197, 94, 0.65))'
          : !active
            ? 'drop-shadow(0 0 6px rgba(244, 63, 94, 0.45))'
            : undefined,
      },
      labelStyle: {
        fill: !active ? '#fda4af' : highlighted ? '#bbf7d0' : '#a1a1aa',
        fontSize: 11,
        fontWeight: highlighted || !active ? 600 : 500,
        fontFamily: 'JetBrains Mono, monospace',
      },
      labelBgStyle: {
        fill: !active ? '#241014' : highlighted ? '#0d2116' : '#141414',
        fillOpacity: 0.94,
        stroke: !active ? 'rgba(244,63,94,0.4)' : highlighted ? 'rgba(34,197,94,0.4)' : '#27272a',
        strokeWidth: 1,
      },
      labelBgPadding: [6, 4],
      labelBgBorderRadius: 6,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 18,
        height: 18,
        color: !active ? '#f43f5e' : highlighted ? '#22c55e' : '#737373',
      },
    };
  });
}

function FlowCanvas({ network, highlightPath, onSelectLink }) {
  const routers = network?.routers || [];
  const links = network?.links || [];
  const builtNodes = useMemo(
    () => layoutNodes(routers, highlightPath),
    [routers, highlightPath],
  );
  const builtEdges = useMemo(
    () => layoutEdges(links, highlightPath),
    [links, highlightPath],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(builtNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(builtEdges);
  const { fitView } = useReactFlow();

  useEffect(() => {
    setNodes(layoutNodes(routers, highlightPath));
    setEdges(layoutEdges(links, highlightPath));
  }, [network?.id, routers, links, highlightPath, setNodes, setEdges]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: 0.26, duration: 220 });
    }, 80);
    return () => window.clearTimeout(timer);
  }, [nodes.length, edges.length, fitView, highlightPath]);

  if (!routers.length) {
    return (
      <div className="topology-wrap" style={{ display: 'grid', placeItems: 'center' }}>
        <p className="card-sub">No routers loaded yet.</p>
      </div>
    );
  }

  return (
    <div className="topology-wrap" style={{ width: '100%', minHeight: 420 }}>
      <div className="rw-canvas-overlay">
        <span className="rw-legend-pill">
          <span className="rw-legend-dot is-active" /> Active Packet Path
        </span>
        <span className="rw-legend-pill">
          <span className="rw-legend-dot is-standby" /> Standby OSPF Link
        </span>
        <span className="rw-legend-pill">
          <span className="rw-legend-dot is-severed" /> Severed / Down Link
        </span>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.26 }}
        minZoom={0.3}
        maxZoom={1.6}
        onEdgeClick={(_, edge) => {
          const id = Number(String(edge.id).replace(/^e-/, ''));
          if (!Number.isNaN(id)) onSelectLink?.(id);
        }}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background color="#27272a" gap={22} size={1.2} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export default function TopologyCanvas({ network, highlightPath = [], onSelectLink }) {
  return (
    <ReactFlowProvider key={network?.id || 'empty'}>
      <FlowCanvas
        network={network}
        highlightPath={highlightPath}
        onSelectLink={onSelectLink}
      />
    </ReactFlowProvider>
  );
}
