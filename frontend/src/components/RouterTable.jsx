export default function RouterTable({ routers = [], loading = false }) {
  return (
    <section className="panel">
      <h3>Routers</h3>
      {loading ? (
        <p className="placeholder-note">Loading router inventory…</p>
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Router ID</th>
                <th>Loopback</th>
                <th>Status</th>
                <th>Protocol</th>
              </tr>
            </thead>
            <tbody>
              {routers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="placeholder-note">
                    No router data yet. Start the backend to load inventory.
                  </td>
                </tr>
              ) : (
                routers.map((router) => (
                  <tr key={router.id}>
                    <td className="mono">{router.id}</td>
                    <td className="mono">{router.loopback}</td>
                    <td>
                      <span className={`status-chip ${router.status}`}>
                        {router.status}
                      </span>
                    </td>
                    <td>{router.protocol}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
