import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api.js';

export default function useNetworkLab() {
  const [overview, setOverview] = useState(null);
  const [network, setNetwork] = useState(null);
  const [lab, setLab] = useState(null);
  const [backendOk, setBackendOk] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async (opts = { quiet: false }) => {
    if (!opts.quiet) {
      setLoading(true);
    }
    setError('');
    try {
      await api.getHealth();
      setBackendOk(true);

      let dash;
      try {
        dash = await api.getDashboardOverview();
      } catch {
        // Ensure seed exists, then retry overview.
        await api.seedDefaultNetwork();
        dash = await api.getDashboardOverview();
      }
      setOverview(dash);

      // Lab status is optional — never block topology data on Docker.
      try {
        setLab(await api.getLabStatus());
      } catch {
        setLab({ running: false, status: 'unavailable', message: 'Lab status unavailable' });
      }

      let networkId = dash?.default_network_id;
      if (!networkId) {
        const seeded = await api.seedDefaultNetwork();
        networkId = seeded.id;
        setOverview(await api.getDashboardOverview());
      }

      const detail = await api.getNetwork(networkId);
      setNetwork(detail);
    } catch (err) {
      setBackendOk(false);
      setError(err.message || 'Backend unavailable');
    } finally {
      if (!opts.quiet) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    refresh({ quiet: false });
    const timer = setInterval(() => refresh({ quiet: true }), 20000);
    return () => clearInterval(timer);
  }, [refresh]);

  return {
    overview,
    network,
    setNetwork,
    lab,
    backendOk,
    loading,
    error,
    refresh: () => refresh({ quiet: false }),
    networkId: network?.id,
  };
}
