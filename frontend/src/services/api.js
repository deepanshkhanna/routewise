/**
 * RouteWise API client.
 * Prefer same-origin /api (Vite proxy) to avoid localhost vs 127.0.0.1 CORS issues.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs || 15000;
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const { timeoutMs: _ignored, ...fetchOptions } = options;

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(fetchOptions.body ? { 'Content-Type': 'application/json' } : {}),
        ...(fetchOptions.headers || {}),
      },
    });

    if (!response.ok) {
      const detail = await response.text();
      const error = new Error(detail || `HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  getHealth: () => request('/api/health'),
  getLabStatus: () => request('/api/lab/status'),
  getRouters: () => request('/api/routers'),
  getTopology: () => request('/api/topology'),
  getRoutes: (routerId) => request(`/api/routers/${routerId}/routes`),
  getOspfNeighbors: (routerId) =>
    request(`/api/routers/${routerId}/ospf-neighbors`),

  getDashboardOverview: () => request('/api/dashboard/overview'),
  listNetworks: () => request('/api/networks'),
  getNetwork: (id) => request(`/api/networks/${id}`),
  seedDefaultNetwork: () => request('/api/networks/seed-default', { method: 'POST' }),
  getPaths: (id, source, destination) =>
    request(
      `/api/networks/${id}/paths?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}`,
    ),
  optimizePath: (id, source, destination) =>
    request(
      `/api/networks/${id}/optimize?source=${encodeURIComponent(source)}&destination=${encodeURIComponent(destination)}`,
    ),
  disableLink: (id, linkId) =>
    request(`/api/networks/${id}/simulate/links/${linkId}/disable`, { method: 'POST' }),
  enableLink: (id, linkId) =>
    request(`/api/networks/${id}/simulate/links/${linkId}/enable`, { method: 'POST' }),
  ping: (id, source, destination) =>
    request(`/api/networks/${id}/diagnostics/ping`, {
      method: 'POST',
      body: JSON.stringify({ source, destination }),
    }),
  traceroute: (id, source, destination) =>
    request(`/api/networks/${id}/diagnostics/traceroute`, {
      method: 'POST',
      body: JSON.stringify({ source, destination }),
    }),
  getEvents: (id) => request(`/api/networks/${id}/events`),
  getStaticRoutes: (id) => request(`/api/networks/${id}/static-routes`),
  addStaticRoute: (id, body) =>
    request(`/api/networks/${id}/static-routes`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getInfrastructure: () => request('/api/lab/infrastructure'),
  getProtocolReadiness: () => request('/api/lab/protocols'),
  inspectLab: () => request('/api/lab/inspect'),
  deployLab: () => request('/api/lab/deploy', { method: 'POST', timeoutMs: 300000 }),
  destroyLab: () => request('/api/lab/destroy', { method: 'POST', timeoutMs: 180000 }),
  restartLab: () => request('/api/lab/restart', { method: 'POST', timeoutMs: 360000 }),

  getFirewallStatus: (id) => request(`/api/networks/${id}/firewall/status`),
  getFirewallRules: (id) => request(`/api/networks/${id}/firewall/rules`),
  createFirewallRule: (id, body) =>
    request(`/api/networks/${id}/firewall/rules`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  deleteFirewallRule: (id, ruleId) =>
    request(`/api/networks/${id}/firewall/rules/${ruleId}`, { method: 'DELETE' }),
  enableFirewallRule: (id, ruleId) =>
    request(`/api/networks/${id}/firewall/rules/${ruleId}/enable`, { method: 'POST' }),
  disableFirewallRule: (id, ruleId) =>
    request(`/api/networks/${id}/firewall/rules/${ruleId}/disable`, { method: 'POST' }),
  testFirewall: (id, body) =>
    request(`/api/networks/${id}/firewall/test`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  applyFirewall: (id) =>
    request(`/api/networks/${id}/firewall/apply`, { method: 'POST', timeoutMs: 60000 }),
};

export default api;
