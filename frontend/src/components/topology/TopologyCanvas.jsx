import { useEffect, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import RouterNode from './RouterNode.jsx';

const nodeTypes = { router: RouterNode };

function layoutNodes(routers) {
  const positions = {
    R1: { x: 280, y: 40 },
    R2: { x: 80, y: 280 },
    R3: { x: 480, y: 280 },
  };
  return (routers || []).map((router, index) => ({
    id: String(router.name),
    type: 'router',
    position: positions[router.name] || { x: 120 + index * 160, y: 160 },
    data: {
      label: router.name,
      loopback: router.loopback,
      status: router.status,
      protocol: router.protocol,
    },
    draggable: true,
  }));
}

function layoutEdges(links, highlightPath = []) {
  const pathSet = new Set();
  for (let i = 0; i < highlightPath.length - 1; i += 1) {
    pathSet.add(`${highlightPath[i]}-${highlightPath[i + 1]}`);
    pathSet.add(`${highlightPath[i + 1]}-${highlightPath[i]}`);
  }
  return (links || []).map((link) => {
    const key = `${link.source_router}-${link.target_router}`;
    const active = link.enabled && link.status === 'up';
    const highlighted = pathSet.has(key);
    return {
      id: `e-${link.id}`,
      source: String(link.source_router),
      target: String(link.target_router),
      label: link.subnet,
      animated: Boolean(highlighted),
      style: {
        stroke: !active ? '#f43f5e' : highlighted ? '#fafafa' : '#737373',
        strokeWidth: highlighted ? 2.8 : 2,
        strokeDasharray: active ? undefined : '6 4',
      },
      labelStyle: { fill: '#a1a1aa', fontSize: 11, fontWeight: 500 },
      labelBgStyle: { fill: '#141414', fillOpacity: 0.9 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: 18,
        height: 18,
        color: highlighted ? '#fafafa' : '#737373',
      },
    };
  });
}

function FlowCanvas({ network, highlightPath, onSelectLink }) {
  const routers = network?.routers || [];
  const links = network?.links || [];
  const builtNodes = useMemo(() => layoutNodes(routers), [routers]);
  const builtEdges = useMemo(
    () => layoutEdges(links, highlightPath),
    [links, highlightPath],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(builtNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(builtEdges);
  const { fitView } = useReactFlow();

  useEffect(() => {
    setNodes(layoutNodes(routers));
    setEdges(layoutEdges(links, highlightPath));
  }, [network?.id, routers, links, highlightPath, setNodes, setEdges]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: 0.25, duration: 200 });
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
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        minZoom={0.3}
        maxZoom={1.6}
        onEdgeClick={(_, edge) => {
          const id = Number(String(edge.id).replace(/^e-/, ''));
          if (!Number.isNaN(id)) onSelectLink?.(id);
        }}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background color="#3f3f46" gap={20} size={1} />
        <MiniMap
          pannable
          zoomable
          maskColor="rgba(0,0,0,.6)"
          nodeColor={(n) => (n.data?.status === 'down' ? '#f43f5e' : '#a1a1aa')}
          style={{ background: '#111', border: '1px solid #27272a' }}
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export default function TopologyCanvas({ network, highlightPath = [], onSelectLink }) {
  // Remount when network identity changes so React Flow always picks up nodes.
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
