const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${base}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers }, signal: AbortSignal.timeout(15000) });
  } catch {
    throw new Error('Unable to connect to the Factory Network backend. Please try again.');
  }
  let result;
  try { result = await response.json(); } catch { throw new Error('Unable to connect to the Factory Network backend. Check that Flask is running.'); }
  if (!response.ok) throw new Error(result.message || 'Unable to complete the request. Please try again.');
  return result;
}

export const api = {
  dashboard: () => request('/dashboard'),
  productionLines: () => request('/production-lines'),
  switches: (filters = {}) => request(`/switches?${new URLSearchParams(filters)}`),
  addProductionLine: data => request('/production-lines', { method: 'POST', body: JSON.stringify(data) }),
  addSwitch: data => request('/switches', { method: 'POST', body: JSON.stringify(data) }),
};
