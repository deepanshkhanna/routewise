import { Bell, Moon, Search, Settings, Wifi, WifiOff, Loader2 } from 'lucide-react';

export default function Header({ backendOk, labRunning, labChecking = false }) {
  const frrBadge = labRunning
    ? { className: 'ok', label: 'FRR up', Icon: Wifi }
    : labChecking
      ? { className: 'warn', label: 'FRR checking', Icon: Loader2 }
      : { className: 'warn', label: 'FRR down', Icon: WifiOff };
  const FrrIcon = frrBadge.Icon;

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
        <span className={`badge ${frrBadge.className}`}>
          {labChecking && !labRunning ? (
            <Loader2 size={12} className="rw-spin" />
          ) : (
            <FrrIcon size={12} />
          )}
          {frrBadge.label}
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
