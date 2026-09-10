import { useCallback, useEffect, useRef, useState } from 'react';
import { PageHeader } from '../components/layout/AppShell';
import { GlassCard, SummaryCard } from '../components/ui/Cards';
import Button from '../components/ui/Button';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import StatusBadge from '../components/ui/StatusBadge';
import ProductionLineTable from '../components/ProductionLineTable';
import AddProductionLine from '../components/forms/AddProductionLine';
import AddSwitch from '../components/forms/AddSwitch';
import { api } from '../services/api';

export default function Dashboard({ linesOnly = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [form, setForm] = useState(null);
  const [detail, setDetail] = useState(null);
  const requests = useRef({ refresh: 0, detail: 0 });

  const refresh = useCallback(() => {
    const id = ++requests.current.refresh;

    return Promise.all([api.dashboard(), api.productionLines()]).then(([summary, lines]) => {
      if (id === requests.current.refresh) { setData({ summary, lines }); setError(''); }
    }).catch(failure => { if (id === requests.current.refresh) setError(failure.message); })
      .finally(() => { if (id === requests.current.refresh) setLoading(false); });
  }, []);
  useEffect(() => { const tokens = requests.current; refresh(); return () => { tokens.refresh++; tokens.detail++; }; }, [refresh]);
  function saved(text) { setForm(null); setMessage(text); setLoading(true); refresh(); }
  function closeDetail() { requests.current.detail++; setDetail(null); }
  async function view(row) {
    const id = ++requests.current.detail;
    setDetail({ title: `${row.name} — Switches`, loading: true, rows: [] });
    try { const rows = await api.switches({ production_line: row.id }); if (id === requests.current.detail) setDetail({ title: `${row.name} — Switches`, rows }); }
    catch (failure) { if (id === requests.current.detail) setDetail({ title: `${row.name} — Switches`, error: failure.message, rows: [] }); }
  }
  const rows = data?.lines.map(line => ({ ...line, supportingInfo: line.description, total: line.total_switches, vendor: line.switch_models.join(' · ') })) || [];
  return <>
    <PageHeader eyebrow="FACTORY NETWORK" title={linesOnly ? 'Production lines' : 'Network overview'} action={<div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => setForm('line')}>Add Production Line</Button><Button disabled={!data?.lines.length || loading} onClick={() => setForm('switch')}>Add Switch</Button></div>} />
    {message && <p className="preview-message mb-4" role="status">{message}</p>}
    {error && <GlassCard className="panel mb-4"><p role="alert">{error}</p><p className="muted">{data ? 'Displayed data may be out of date.' : 'Check that the backend is running.'}</p><Button variant="secondary" onClick={() => { setLoading(true); refresh(); }}>Retry</Button></GlassCard>}
    {loading && <p className="muted mb-4" role="status">{data ? 'Refreshing data…' : 'Loading factory network…'}</p>}
    {data && <>
      {!linesOnly && <div className="summary-grid mb-8">{[['total_switches', 'TOTAL SWITCHES', 'total'], ['active', 'ACTIVE', 'active'], ['offline', 'OFFLINE', 'offline'], ['spare', 'SPARE', 'spare']].map(([key, title, variant]) => <SummaryCard key={key} title={title} value={data.summary[key]} variant={variant} description="Saved switches" />)}</div>}
      {!data.lines.length && <p className="muted mb-4">Add a Production Line first, then add your first Switch.</p>}
      <ProductionLineTable rows={rows} onView={view} onSelectionPreview={count => setDetail({ title: 'Selection preview', message: `${count} production line(s) selected. Bulk actions are not implemented.`, rows: [] })} />
    </>}
    {form === 'line' && <AddProductionLine onClose={() => setForm(null)} onSaved={saved} />}
    {form === 'switch' && <AddSwitch lines={data.lines} onClose={() => setForm(null)} onSaved={saved} />}
    <ConfirmDialog open={Boolean(detail)} title={detail?.title || 'Switches'} onClose={closeDetail} onConfirm={closeDetail} confirmLabel="Close">
      {detail?.loading ? <p role="status">Loading switches…</p> : detail?.error ? <p role="alert">{detail.error}</p> : detail?.message ? <p>{detail.message}</p> : detail?.rows.length ? <ul className="form-stack">{detail.rows.map(row => <li key={row.id}><strong>{row.hostname}</strong><p>{row.vendor} {row.model}</p><StatusBadge status={row.status} /></li>)}</ul> : <p>No switches assigned to this Production Line.</p>}
    </ConfirmDialog>
  </>;
}
