import { useCallback, useEffect, useState } from 'react';
import { api } from '../services/api.js';

export default function useNetworkLab() {
  const [overview, setOverview] = useState(null);
  const [network, setNetwork] = useState(null);
  const [lab, setLab] = useState(null);
  const [backendOk, setBackendOk] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refreshLab = useCallback(async () => {
    try {
      const labData = await api.getLabStatus();
      setLab(labData);
      return labData;
    } catch {
      setLab((prev) => {
        if (prev?.running) return prev; // keep last good FRR-up state briefly
        return { running: false, status: 'unavailable', message: 'Lab status unavailable' };
      });
      return null;
    }
  }, []);

  const refresh = useCallback(
    async (opts = { quiet: false }) => {
      if (!opts.quiet) {
        setLoading(true);
      }
      setError('');

      let healthAlive = false;
      try {
        await api.getHealth();
        healthAlive = true;
        setBackendOk(true);
      } catch (err) {
        setBackendOk(false);
        setError(err.message || 'Backend API unreachable on port 8000');
        if (!opts.quiet) {
          setLoading(false);
        }
        return;
      }

      // Independent FRR poll — never blocks topology load.
      refreshLab();

      try {
        let dash;
        try {
          dash = await api.getDashboardOverview();
        } catch {
          await api.seedDefaultNetwork();
          dash = await api.getDashboardOverview();
        }
        setOverview(dash);

        // Prefer overview.lab_running for immediate FRR badge update.
        if (typeof dash?.lab_running === 'boolean') {
          setLab((prev) => ({
            ...(prev || {}),
            running: dash.lab_running,
            status: dash.lab_running ? 'running' : prev?.status || 'stopped',
            message: dash.lab_running
              ? 'RouteWise Docker lab is running.'
              : prev?.message || 'Lab not running',
          }));
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
        if (healthAlive) {
          setBackendOk(true);
        }
        setError(err.message || 'Failed to load topology data');
      } finally {
        if (!opts.quiet) {
          setLoading(false);
        }
      }
    },
    [refreshLab],
  );

  useEffect(() => {
    refresh({ quiet: false });
    const dataTimer = setInterval(() => refresh({ quiet: true }), 15000);
    const labTimer = setInterval(() => refreshLab(), 8000);
    return () => {
      clearInterval(dataTimer);
      clearInterval(labTimer);
    };
  }, [refresh, refreshLab]);

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
