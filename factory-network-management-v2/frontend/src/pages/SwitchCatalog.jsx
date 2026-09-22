import { useCallback, useEffect, useRef, useState } from 'react';
import { PageHeader } from '../components/layout/AppShell';
import { GlassCard } from '../components/ui/Cards';
import Button from '../components/ui/Button';
import DataTable from '../components/ui/DataTable';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import DeleteCatalogs from '../components/forms/DeleteCatalogs';
import CatalogImage from '../components/CatalogImage';
import CatalogForm from '../components/forms/CatalogForm';
import { api } from '../services/api';

const searchKeys = ['name', 'vendor', 'model'];
export default function SwitchCatalog() {
  const [rows, setRows] = useState([]);
  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState([]);
  const [deleting, setDeleting] = useState(false);
  function cancelSelection() { setSelected([]); setSelecting(false); }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [form, setForm] = useState(null);
  const [detail, setDetail] = useState(null);
  const [message, setMessage] = useState('');
  const requests = useRef({ list: 0, detail: 0 });
  const refresh = useCallback(() => {
    const token = ++requests.current.list;
    return api.catalogs().then(result => { if (token === requests.current.list) { setRows(result); setError(''); } })
      .catch(failure => { if (token === requests.current.list) setError(failure.message); })
      .finally(() => { if (token === requests.current.list) setLoading(false); });
  }, []);
  useEffect(() => { const tokens = requests.current; refresh(); return () => { tokens.list++; tokens.detail++; }; }, [refresh]);
  function closeDetail() { requests.current.detail++; setDetail(null); }
  async function view(row) {
    const token = ++requests.current.detail;
    setDetail({ loading: true, name: row.name });
    try { const result = await api.catalog(row.id); if (token === requests.current.detail) setDetail(result); }
    catch (failure) { if (token === requests.current.detail) setDetail({ name: row.name, error: failure.message }); }
  }
  const columns = [
    { key: 'name', label: 'Model Name', sortable: true, render: row => <div className="flex items-center gap-2"><CatalogImage url={row.image_url} name={row.name} compact /><strong className="cell-name">{row.name}</strong></div> },
    { key: 'vendor', label: 'Vendor', sortable: true },
    { key: 'model', label: 'Model', sortable: true },
    { key: 'switch_count', label: 'Switches', sortable: true },
    { key: 'actions', label: 'Actions', action: true, render: row => <div className="flex gap-2"><Button variant="ghost" aria-label={`View ${row.name}`} onClick={() => view(row)}>View</Button><Button variant="ghost" aria-label={`Edit ${row.name}`} onClick={() => setForm({ entry: row })}>Edit</Button></div> },
  ];
  return <>
    <PageHeader eyebrow="FACTORY NETWORK" title="Switch Catalog" action={<Button onClick={() => setForm({ entry: null })}>+ Add Model</Button>} />
    <p className="muted mb-4">Manage switch models used in the factory.</p>
    {message && <p className="preview-message mb-4" role="status">{message}</p>}
    {error && <div className="mb-4"><p role="alert">{error}</p><Button variant="secondary" onClick={refresh}>Retry</Button></div>}
    {loading && <p role="status">Loading switch models…</p>}
    <GlassCard className="table-card"><DataTable caption="Switch Catalog" rows={rows} columns={columns} selectionMode={selecting} selected={selected} onSelectionChange={setSelected} selectAllVisible clearSelectionOnViewChange filterActions={<div className="flex items-center flex-wrap gap-2">{selecting ? <><span role="status">{selected.length} selected</span><Button variant="danger" disabled={!selected.length || loading} onClick={() => setDeleting(true)}>Delete Selected ({selected.length})</Button><Button variant="ghost" onClick={cancelSelection}>Cancel</Button></> : <Button variant="secondary" onClick={() => setSelecting(true)}>Select</Button>}</div>} searchKeys={searchKeys} searchPlaceholder="Search models…" emptyTitle="No switch models found." emptyDescription={rows.length ? 'Try changing your search.' : 'Add your first switch model to start building the catalog.'} /></GlassCard>
    {deleting && <DeleteCatalogs ids={selected} onClose={() => setDeleting(false)} onSaved={result => {
      setDeleting(false); cancelSelection();
      setMessage(`${result.deleted.length} model(s) deleted.${result.blocked.length ? ` Kept: ${result.blocked.map(row => `${row.name} — ${row.reason}`).join('; ')}` : ''}`);
      refresh();
    }} />}
    {form && <CatalogForm entry={form.entry} onClose={() => setForm(null)} onSaved={() => { setMessage(form.entry ? 'Switch model updated.' : 'Switch model added.'); setForm(null); setSelected([]); refresh(); }} />}
    <ConfirmDialog open={Boolean(detail)} title={detail?.name || 'Switch Model'} onClose={closeDetail} onConfirm={closeDetail} confirmLabel="Close" showCancel={false}>
      {detail?.loading ? <p role="status">Loading model…</p> : detail?.error ? <p role="alert">{detail.error}</p> : detail && <><CatalogImage url={detail.image_url} name={detail.name} /><dl className="form-stack">{[['vendor', 'Vendor'], ['model', 'Model'], ['description', 'Description'], ['switch_count', 'Switches in use']].map(([key, label]) => <div key={key}><dt className="label">{label}</dt><dd className="break-words whitespace-pre-wrap">{detail[key] === 0 ? 0 : detail[key] || '—'}</dd></div>)}</dl></>}
    </ConfirmDialog>
  </>;
}
