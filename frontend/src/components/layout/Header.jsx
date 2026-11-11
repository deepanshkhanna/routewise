import { Bell, Moon, Search, Settings, Wifi, WifiOff } from 'lucide-react';

export default function Header({ backendOk, labRunning }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">RW</span>
        <span>RouteWise</span>
      </div>
      <div className="search-pill" role="search">
        <Search size={14} />
        <span>Search routers, paths, events…</span>
        <kbd>⌘K</kbd>
      </div>
      <div className="header-actions">
        <span className={`badge ${backendOk ? 'ok' : 'err'}`}>
          <span className="dot" />
          API {backendOk ? 'online' : 'offline'}
        </span>
        <span className={`badge ${labRunning ? 'ok' : 'warn'}`}>
          {labRunning ? <Wifi size={12} /> : <WifiOff size={12} />}
          FRR {labRunning ? 'up' : 'down'}
        </span>
        <button type="button" className="btn-icon" aria-label="Notifications">
          <Bell size={16} />
        </button>
        <button type="button" className="btn-icon" aria-label="Theme">
          <Moon size={16} />
        </button>
        <button type="button" className="btn-icon" aria-label="Settings">
          <Settings size={16} />
        </button>
      </div>
    </header>
  );
}
