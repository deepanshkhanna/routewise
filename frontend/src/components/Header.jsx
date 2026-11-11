export default function Header({ backendStatus, labStatus }) {
  const backendClass =
    backendStatus === 'connected' ? 'ok' : backendStatus === 'loading' ? 'warn' : 'err';
  const labClass =
    labStatus === 'running' ? 'ok' : labStatus === 'loading' ? 'warn' : 'err';

  const backendLabel =
    backendStatus === 'connected'
      ? 'Backend connected'
      : backendStatus === 'loading'
        ? 'Backend checking…'
        : 'Backend offline';

  const labLabel =
    labStatus === 'running'
      ? 'Lab running'
      : labStatus === 'loading'
        ? 'Lab checking…'
        : 'Lab stopped';

  return (
    <header className="header">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true" />
        <h1>RouteWise</h1>
        <span>routing · path · ospf</span>
      </div>
      <div className="header-indicators">
        <span className={`pill ${backendClass}`}>
          <span className="dot" />
          {backendLabel}
        </span>
        <span className={`pill ${labClass}`}>
          <span className="dot" />
          {labLabel}
        </span>
      </div>
    </header>
  );
}
