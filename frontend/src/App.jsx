import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Header from './components/layout/Header.jsx';
import Sidebar from './components/layout/Sidebar.jsx';
import useNetworkLab from './hooks/useNetworkLab.js';
import Dashboard from './pages/Dashboard.jsx';
import TopologyPage from './pages/TopologyPage.jsx';
import RoutingPage from './pages/RoutingPage.jsx';
import { OptimizationPage, PathExplorerPage } from './pages/PathOptimizePages.jsx';
import SimulationPage from './pages/SimulationPage.jsx';
import FirewallPage from './pages/FirewallPage.jsx';
import {
  AnalyticsPage,
  EventsPage,
  ReportsPage,
  SettingsPage,
} from './pages/SecondaryPages.jsx';

function AppRoutes({
  overview,
  network,
  setNetwork,
  lab,
  backendOk,
  loading,
  error,
  refresh,
}) {
  const location = useLocation();

  return (
    <Routes location={location} key={location.pathname}>
      <Route
        path="/"
        element={
          <Dashboard
            overview={overview}
            network={network}
            lab={lab}
            loading={loading}
            error={error}
          />
        }
      />
      <Route
        path="/topology"
        element={
          <TopologyPage network={network} setNetwork={setNetwork} refresh={refresh} />
        }
      />
      <Route path="/routing" element={<RoutingPage network={network} />} />
      <Route path="/paths" element={<PathExplorerPage network={network} />} />
      <Route path="/optimize" element={<OptimizationPage network={network} />} />
      <Route
        path="/simulation"
        element={
          <SimulationPage network={network} setNetwork={setNetwork} refresh={refresh} />
        }
      />
      <Route path="/firewall" element={<FirewallPage network={network} />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route path="/events" element={<EventsPage network={network} />} />
      <Route path="/reports" element={<ReportsPage network={network} overview={overview} />} />
      <Route
        path="/settings"
        element={<SettingsPage backendOk={backendOk} lab={lab} refresh={refresh} />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  const {
    overview,
    network,
    setNetwork,
    lab,
    backendOk,
    loading,
    error,
    refresh,
  } = useNetworkLab();

  return (
    <div className="app-root">
      <Header backendOk={backendOk} labRunning={Boolean(lab?.running)} />
      <Sidebar />
      <main className="app-main">
        <AppRoutes
          overview={overview}
          network={network}
          setNetwork={setNetwork}
          lab={lab}
          backendOk={backendOk}
          loading={loading}
          error={error}
          refresh={refresh}
        />
      </main>
    </div>
  );
}
