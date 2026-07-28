/* Shared API client, auth-state helpers, and small UI utilities used
   across every page of the FPL Assistant frontend. */

const API_BASE = window.FPL_API_BASE || 'http://localhost:5000/api';

const Auth = {
  TOKEN_KEY: 'fpl_token',
  USER_KEY: 'fpl_user',

  getToken() { return localStorage.getItem(this.TOKEN_KEY); },
  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setSession(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },
  isLoggedIn() { return !!this.getToken(); },
  requireAuth() {
    if (!this.isLoggedIn()) window.location.href = 'index.html';
  },
};

async function apiRequest(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && Auth.getToken()) headers.Authorization = `Bearer ${Auth.getToken()}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error('Cannot reach the server. Is the backend running?');
  }

  let data = {};
  try { data = await res.json(); } catch (_) { /* no body */ }

  if (res.status === 401 && auth) {
    Auth.clear();
    window.location.href = 'index.html';
    return;
  }
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

const Api = {
  register: (payload) => apiRequest('/auth/register', { method: 'POST', body: payload, auth: false }),
  login: (payload) => apiRequest('/auth/login', { method: 'POST', body: payload, auth: false }),
  me: () => apiRequest('/auth/me'),

  players: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/players${qs ? `?${qs}` : ''}`, { auth: false });
  },
  playerDetail: (id) => apiRequest(`/players/${id}`, { auth: false }),
  comparePlayers: (playerIds) => apiRequest('/players/compare', { method: 'POST', body: { playerIds }, auth: false }),

  teams: () => apiRequest('/teams', { auth: false }),
  fixtures: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiRequest(`/fixtures${qs ? `?${qs}` : ''}`, { auth: false });
  },

  mySquads: () => apiRequest('/squads'),
  createSquad: (payload) => apiRequest('/squads', { method: 'POST', body: payload }),
  updateSquad: (id, payload) => apiRequest(`/squads/${id}`, { method: 'PUT', body: payload }),
  deleteSquad: (id) => apiRequest(`/squads/${id}`, { method: 'DELETE' }),
  rateSquad: (playerIds) => apiRequest('/squads/rate', { method: 'POST', body: { playerIds }, auth: false }),
  optimiseSquad: (payload) => apiRequest('/squads/optimise', { method: 'POST', body: payload, auth: false }),

  watchlist: () => apiRequest('/watchlist'),
  addWatchlist: (playerId, note) => apiRequest('/watchlist', { method: 'POST', body: { playerId, note } }),
  removeWatchlist: (playerId) => apiRequest(`/watchlist/${playerId}`, { method: 'DELETE' }),
};

/* ---------- Toasts ---------- */
function toast(message, type = 'info') {
  let stack = document.querySelector('.toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

/* ---------- Formatting helpers ---------- */
const fmt = {
  money: (n) => `£${Number(n).toFixed(1)}m`,
  posBadgeClass: (pos) => `badge badge-${(pos || '').toLowerCase()}`,
  fdrBadgeClass: (fdr) => `badge badge-fdr-${fdr}`,
  initials: (name) => (name || '?').split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase(),
};
