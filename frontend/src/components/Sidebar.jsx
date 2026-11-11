const ITEMS = [
  'Dashboard',
  'Network Topology',
  'Routers',
  'Path Explorer',
  'Optimization',
  'Simulation Lab',
  'Events',
  'Settings',
];

export default function Sidebar({ active, onSelect }) {
  return (
    <aside className="sidebar">
      <nav aria-label="Primary">
        <ul className="nav-list">
          {ITEMS.map((item) => (
            <li key={item}>
              <button
                type="button"
                className={`nav-item${active === item ? ' active' : ''}`}
                onClick={() => onSelect(item)}
              >
                {item}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
