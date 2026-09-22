const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${base}${path}`, { ...options, headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers }, signal: AbortSignal.timeout(15000) });
  } catch {
    throw new Error('Unable to connect to the Factory Network backend. Please try again.');
  }
  let result;
  try { result = await response.json(); } catch { throw new Error('Unable to connect to the Factory Network backend. Check that Flask is running.'); }
  if (!response.ok) throw new Error(result.message || 'Unable to complete the request. Please try again.');
  return result;
}

export const mediaUrl = path => path?.startsWith('/api/') ? `${base}${path.slice(4)}` : path;

export const passportPath = uid => `/passport/${encodeURIComponent(uid)}`;

async function download(path) {
  let response;
  try { response = await fetch(`${base}${path}`, { signal: AbortSignal.timeout(30000) }); }
  catch { throw new Error('Unable to download. Check the backend connection and try again.'); }
  if (!response.ok) {
    let result; try { result = await response.json(); } catch { /* Use the readable fallback. */ }
    throw new Error(result?.message || 'Unable to download the export file.');
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'fnms_switch_inventory.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function importFile(file, fingerprint) {
  const data = new FormData(); data.set('file', file);
  if (fingerprint) data.set('fingerprint', fingerprint);
  return data;
}
export const api = {
  importTemplate: () => download('/switches/import/template'),
  previewImport: file => request('/switches/import/preview', { method: 'POST', body: importFile(file) }),
  confirmImport: (file, fingerprint) => request('/switches/import/confirm', { method: 'POST', body: importFile(file, fingerprint) }),
  exportInventory: (scope, criteria, format = 'csv') => download(`/switches/export?${new URLSearchParams({ scope, search: criteria.query, ...criteria.filters, format })}`),
  previewCatalogDelete: ids => request('/switch-catalog/delete-preview', { method: 'POST', body: JSON.stringify({ ids }) }),
  deleteCatalogs: data => request('/switch-catalog/delete', { method: 'POST', body: JSON.stringify(data) }),
  catalogs: () => request('/switch-catalog'),
  catalog: id => request(`/switch-catalog/${encodeURIComponent(id)}`),
  addCatalog: data => request('/switch-catalog', { method: 'POST', body: data instanceof FormData ? data : JSON.stringify(data) }),
  editCatalog: (id, data) => request(`/switch-catalog/${encodeURIComponent(id)}`, { method: 'PATCH', body: data instanceof FormData ? data : JSON.stringify(data) }),
  passport: uid => request(`/passport/${encodeURIComponent(uid)}`),
  passportQr: uid => `${base}/passport/${encodeURIComponent(uid)}/qr.png`,
  moveSwitch: (id, data) => request(`/switches/${encodeURIComponent(id)}/move`, { method: 'POST', body: JSON.stringify(data) }),
  editProductionLine: (id, data) => request(`/production-lines/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateSwitchStatus: (id, status) => request(`/switches/${encodeURIComponent(id)}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  pinStatus: () => request('/settings/delete-pin/status'),
  setupPin: data => request('/settings/delete-pin/setup', { method: 'POST', body: JSON.stringify(data) }),
  changePin: data => request('/settings/delete-pin/change', { method: 'POST', body: JSON.stringify(data) }),
  deleteSwitches: data => request('/switches/delete', { method: 'POST', body: JSON.stringify(data) }),
  restoreSwitches: ids => request('/switches/restore', { method: 'POST', body: JSON.stringify({ switch_ids: ids }) }),
  dashboard: () => request('/dashboard'),
  productionLines: () => request('/production-lines'),
  switches: (filters = {}) => request(`/switches?${new URLSearchParams(filters)}`),
  switch: id => request(`/switches/${encodeURIComponent(id)}`),
  addProductionLine: data => request('/production-lines', { method: 'POST', body: JSON.stringify(data) }),
  editSwitch: (id, data) => request(`/switches/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) }),
  addSwitch: data => request('/switches', { method: 'POST', body: JSON.stringify(data) }),
};
