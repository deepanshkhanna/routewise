import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const data = [
  { t: '00', latency: 12, loss: 0.2 },
  { t: '04', latency: 15, loss: 0.4 },
  { t: '08', latency: 22, loss: 0.8 },
  { t: '12', latency: 18, loss: 0.3 },
  { t: '16', latency: 28, loss: 1.1 },
  { t: '20', latency: 17, loss: 0.5 },
  { t: '24', latency: 14, loss: 0.2 },
];

export default function TrafficAreaChart() {
  return (
    <div style={{ width: '100%', height: 260 }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="latFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fafafa" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#fafafa" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="lossFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#a1a1aa" stopOpacity={0.22} />
              <stop offset="100%" stopColor="#a1a1aa" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#27272a" vertical={false} />
          <XAxis dataKey="t" stroke="#71717a" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis stroke="#71717a" tickLine={false} axisLine={false} fontSize={12} />
          <Tooltip
            contentStyle={{
              background: '#141414',
              border: '1px solid #27272a',
              borderRadius: 10,
              color: '#fafafa',
            }}
          />
          <Area
            type="monotone"
            dataKey="latency"
            stroke="#fafafa"
            fill="url(#latFill)"
            strokeWidth={2}
            name="Latency ms"
          />
          <Area
            type="monotone"
            dataKey="loss"
            stroke="#a1a1aa"
            fill="url(#lossFill)"
            strokeWidth={1.5}
            name="Loss %"
          />
        </AreaChart>
      </ResponsiveContainer>
      <p className="card-sub" style={{ marginTop: 8 }}>
        Illustrative telemetry series for UI — not live FRR counters.
      </p>
    </div>
  );
}
