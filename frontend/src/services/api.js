/**
 * RouteWise API client.
 * Prefer same-origin /api (Vite proxy) to avoid localhost vs 127.0.0.1 CORS issues.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const DIRECT_BACKEND = 'http://127.0.0.1:8000';

async function fetchWithTimeout(url, fetchOptions, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(fetchOptions.body ? { 'Content-Type': 'application/json' } : {}),
        ...(fetchOptions.headers || {}),
      },
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function request(path, options = {}) {
  const timeoutMs = options.timeoutMs || 25000;
  const { timeoutMs: _ignored, ...fetchOptions } = options;
  const primaryUrl = `${API_BASE}${path}`;

  let response;
  try {
    response = await fetchWithTimeout(primaryUrl, fetchOptions, timeoutMs);
  } catch (err) {
    // Fallback to direct 127.0.0.1:8000 if proxy or localhost resolution hiccups.
    if (primaryUrl !== `${DIRECT_BACKEND}${path}`) {
      response = await fetchWithTimeout(`${DIRECT_BACKEND}${path}`, fetchOptions, timeoutMs);
    } else {
      throw err;
    }
  }

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
  failRouter: (id, routerName) =>
    request(`/api/networks/${id}/simulate/routers/${encodeURIComponent(routerName)}/fail`, {
      method: 'POST',
    }),
  restoreRouter: (id, routerName) =>
    request(`/api/networks/${id}/simulate/routers/${encodeURIComponent(routerName)}/restore`, {
      method: 'POST',
    }),
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
