import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Network,
  Route as RouteIcon,
  GitBranch,
  Sparkles,
  FlaskConical,
  LineChart,
  Bell,
  FileText,
  Settings,
  Router,
  Shield,
} from 'lucide-react';
import { api } from '../../services/api.js';

const SECTIONS = [
  {
    title: 'Workspace',
    items: [
      { to: '/', label: 'Overview', icon: LayoutDashboard },
      { to: '/topology', label: 'Topology Designer', icon: Network, badge: 'Live' },
      { to: '/routing', label: 'Routing Manager', icon: Router },
      { to: '/paths', label: 'Path Explorer', icon: RouteIcon },
      { to: '/optimize', label: 'Optimization', icon: Sparkles },
      { to: '/simulation', label: 'Simulation Lab', icon: FlaskConical },
      { to: '/firewall', label: 'Firewall & Security', icon: Shield },
    ],
  },
  {
    title: 'Insights',
    items: [
      { to: '/analytics', label: 'Analytics', icon: LineChart },
      { to: '/events', label: 'Events & Alerts', icon: Bell },
      { to: '/reports', label: 'Reports', icon: FileText },
    ],
  },
  {
    title: 'System',
    items: [{ to: '/settings', label: 'Settings & Lab', icon: Settings }],
  },
];

export default function Sidebar() {
  const [mode, setMode] = useState('SOFTWARE_SIMULATION');

  useEffect(() => {
    const load = () => {
      api
        .getInfrastructure()
        .then((infra) => setMode(infra.active_mode || 'SOFTWARE_SIMULATION'))
        .catch(() => setMode('SOFTWARE_SIMULATION'));
    };
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, []);

  return (
    <aside className="app-sidebar">
      {SECTIONS.map((section) => (
        <div key={section.title}>
          <div className="nav-section">{section.title}</div>
          <ul className="nav-list">
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                  >
                    <Icon size={16} strokeWidth={1.75} />
                    <span>{item.label}</span>
                    {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
      <div style={{ marginTop: 'auto', padding: '1rem 0.65rem 0.35rem' }}>
        <div className="card card-pad" style={{ display: 'flex', gap: '0.65rem', alignItems: 'center' }}>
          <GitBranch size={16} />
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>RouteWise Lab</div>
            <div className="card-sub">{mode}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
