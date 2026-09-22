import { useCallback, useEffect, useRef, useState } from 'react';
import { PageHeader } from '../components/layout/AppShell';
import { GlassCard } from '../components/ui/Cards';
import Button from '../components/ui/Button';
import DataTable from '../components/ui/DataTable';
import StatusBadge from '../components/ui/StatusBadge';
import InventoryTransfer from '../components/forms/InventoryTransfer';
import AddSwitch from '../components/forms/AddSwitch';
import MoveSwitch from '../components/forms/MoveSwitch';
import SwitchDetail from '../components/SwitchDetail';
import RecordDate from '../components/RecordDate';
import InlineSwitchStatus from '../components/InlineSwitchStatus';
import PinDialog from '../components/forms/PinDialog';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { api } from '../services/api';

const searchKeys = ['hostname', 'serial_number', 'asset_id', 'vendor', 'model', 'ip_address', 'production_line', 'block'];
const plain = (key, label) => ({ key, label, sortable: true, render: row => row[key] || '—' });
export default function SwitchInventory() {
  const [transfer, setTransfer] = useState(null);
  const [criteria, setCriteria] = useState({ query: '', filters: {} });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [editing, setEditing] = useState(null);
  const [moving, setMoving] = useState(null);
  const [adding, setAdding] = useState(false);
  const [viewId, setViewId] = useState(null);
  const [recycled, setRecycled] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState([]);
  const [deleting, setDeleting] = useState(false);
  const [needsPin, setNeedsPin] = useState(false);
  const [checking, setChecking] = useState(false);
  const [restoreRow, setRestoreRow] = useState(null);
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState('');
  const requests = useRef({ current: 0 });
  const refresh = useCallback(() => {
    const id = ++requests.current.current;
    return Promise.all([api.switches({ deleted: String(recycled) }), api.productionLines()]).then(([switches, lines]) => {
      if (id === requests.current.current) { setData({ switches, lines }); setError(''); }
    }).catch(failure => { if (id === requests.current.current) setError(failure.message); })
      .finally(() => { if (id === requests.current.current) setLoading(false); });
  }, [recycled]);
  useEffect(() => { const token = requests.current; refresh(); return () => { token.current++; }; }, [refresh]);
  function cancelSelection() { setSelecting(false); setSelected([]); }
  function switchMode() { setCriteria({ query: '', filters: {} }); setData(null); setLoading(true); setError(''); setMessage(''); cancelSelection(); setRecycled(value => !value); }
  async function requestDelete() {
    setChecking(true);
    try { const result = await api.pinStatus(); if (result.pin_configured) setDeleting(true); else setNeedsPin(true); }
    catch (failure) { setError(failure.message); }
    finally { setChecking(false); }
  }
  async function restore() {
    if (restoring) return;
    setRestoring(true); setRestoreError('');
    try { await api.restoreSwitches([restoreRow.id]); setRestoreRow(null); saved('Switch restored.'); }
    catch (failure) { setRestoreError(failure.message); }
    finally { setRestoring(false); }
  }
  function saved(text) { setEditing(null); setAdding(false); setMessage(text); setLoading(true); refresh(); }
  const columns = [
    { ...plain('hostname', 'Hostname'), render: row => <span className="cell-name">{row.hostname}</span> },
    plain('serial_number', 'SN'), plain('asset_id', 'Asset ID'),
    { key: 'vendor_model', label: 'Model Type', sortable: true, sortValue: row => `${row.vendor} ${row.model}`, render: row => row.catalog_name || `${row.vendor} ${row.model}` },
    plain('ip_address', 'IP'), plain('production_line', 'PD Line'), plain('block', 'Block'), plain('firmware_version', 'Firmware'),
    { key: 'status', label: 'Status', sortable: true, render: row => <InlineSwitchStatus row={row} onSaved={updated => { setData(previous => previous ? { ...previous, switches: previous.switches.map(item => item.id === updated.id ? updated : item) } : previous); }} /> },
    { key: 'created_at', label: 'Created Date', sortable: true, sortValue: row => Date.parse(row.created_at) || 0, render: row => <RecordDate value={row.created_at} /> },
    { key: 'actions', label: 'Actions', action: true, render: row => <div className="flex gap-2"><Button variant="ghost" aria-label={`View ${row.hostname}`} onClick={() => setViewId(row.id)}>View</Button><Button variant="ghost" aria-label={`Edit ${row.hostname}`} onClick={async () => { try { setEditing(await api.switch(row.id)); } catch (failure) { setError(failure.message); } }}>Edit</Button><Button variant="ghost" aria-label={`Move ${row.hostname}`} onClick={async () => { try { setMoving(await api.switch(row.id)); } catch (failure) { setError(failure.message); } }}>Move</Button></div> },
  ];
  const recycleColumns = [plain('hostname', 'Hostname'), plain('serial_number', 'Serial Number'), plain('production_line', 'Production Line'), plain('block', 'Block'),
    { key: 'status', label: 'Status', sortable: true, render: row => <StatusBadge status={row.status} /> },
    { key: 'deleted_at', label: 'Deleted Date', sortable: true, sortValue: row => Date.parse(row.deleted_at) || 0, render: row => <RecordDate value={row.deleted_at} /> },
    { key: 'restore', label: 'Restore', action: true, render: row => <Button variant="ghost" aria-label={`Restore ${row.hostname}`} onClick={() => { setRestoreError(''); setRestoreRow(row); }}>Restore</Button> },
  ];
  const filters = [{ key: 'production_line', label: 'Production Line', options: data?.lines.map(line => line.name) || [] }, { key: 'status', label: 'Status', options: ['ACTIVE', 'OFFLINE', 'SPARE'] }, { key: 'vendor', label: 'Vendor', options: [...new Set(data?.switches.map(row => row.vendor) || [])].sort() }];
  return <>
    <PageHeader eyebrow="FACTORY NETWORK" title="Switch inventory" action={<Button disabled={!data?.lines.length || loading} onClick={() => setAdding(true)}>Add Switch</Button>} />
    {message && <p className="preview-message mb-4" role="status">{message}</p>}
    {error && <GlassCard className="panel mb-4"><p role="alert">{error}</p>{data && <p className="muted">Displayed data may be out of date.</p>}<Button variant="secondary" onClick={() => { setLoading(true); refresh(); }}>Retry</Button></GlassCard>}
    {loading && <p className="muted mb-4" role="status">{data ? 'Refreshing inventory…' : 'Loading switches…'}</p>}
    {data && <>
      {!data.lines.length && <p className="muted mb-4">Create a Production Line from <a className="underline" href="#/lines">Production Lines</a> before adding a switch.</p>}
      <GlassCard className="table-card"><div className="table-card-header"><div><h3>{recycled ? 'Deleted Switches' : 'Switch records'}</h3><p className="muted">{data.switches.length} {recycled ? 'deleted' : 'saved'} switches</p></div><div className="flex flex-wrap items-center gap-2">
        {!recycled && <><Button variant="secondary" disabled={loading} onClick={() => setTransfer('import')}>Import</Button><Button variant="secondary" disabled={loading} onClick={() => setTransfer('export')}>Export</Button></>}
        <Button variant="secondary" disabled={loading || checking} onClick={switchMode}>{recycled ? 'Back to Inventory' : 'Recycle Bin'}</Button>
        {!recycled && (selecting ? <><span role="status">{selected.length} selected</span><Button variant="danger" disabled={!selected.length || loading || checking} onClick={requestDelete}>Delete</Button><Button variant="ghost" onClick={cancelSelection}>Cancel</Button></> : <Button variant="secondary" disabled={!data.switches.length || loading} onClick={() => setSelecting(true)}>Select</Button>)}
      </div></div>
        <DataTable onCriteriaChange={setCriteria} key={String(recycled)} caption={recycled ? "Deleted Switches" : "Switch Inventory"} columns={recycled ? recycleColumns : columns} selectionMode={selecting && !recycled} selected={selected} onSelectionChange={setSelected} rows={data.switches} searchKeys={searchKeys} searchPlaceholder="Search hostname, serial, asset, vendor, model, IP, line or block" filterDefinitions={filters} emptyTitle={recycled ? "No deleted switches found" : "No switches found"} emptyDescription={data.switches.length ? 'Try changing your search or filters.' : recycled ? 'Deleted switches will appear here.' : 'Add your first switch to start building the inventory.'} />
      </GlassCard>
    </>}
    {transfer && <InventoryTransfer mode={transfer} criteria={criteria} onClose={() => setTransfer(null)} onImported={count => { setTransfer(null); cancelSelection(); saved(`Import Complete: ${count} Switches imported successfully.`); }} />}
    {needsPin && <ConfirmDialog open title="Delete PIN not configured" confirmLabel="Go to Settings" onClose={() => setNeedsPin(false)} onConfirm={() => { window.location.hash = '#/settings'; }}><p>Please set a 6-digit Delete PIN in Settings before deleting switches.</p></ConfirmDialog>}
    {deleting && <PinDialog mode="delete" count={selected.length} onClose={() => setDeleting(false)} onSubmit={values => api.deleteSwitches({ ...values, switch_ids: selected })} onSaved={() => { setDeleting(false); cancelSelection(); saved('Switches moved to Recycle Bin.'); }} />}
    {restoreRow && <ConfirmDialog open title={`Restore ${restoreRow.hostname}?`} confirmLabel="Restore" onClose={() => setRestoreRow(null)} onConfirm={restore} busy={restoring}><p>This switch will return to the active inventory.</p>{restoreError && <p role="alert" className="field-error">{restoreError}</p>}</ConfirmDialog>}
    {moving && <MoveSwitch record={moving} lines={data.lines} onClose={() => setMoving(null)} onSaved={() => { setMoving(null); saved('Switch moved successfully.'); }} />}
    {editing && <AddSwitch record={editing} lines={data.lines} onClose={() => setEditing(null)} onSaved={saved} />}
    {adding && <AddSwitch lines={data.lines} onClose={() => setAdding(false)} onSaved={saved} />}
    {viewId !== null && <SwitchDetail key={viewId} switchId={viewId} onClose={() => setViewId(null)} />}
  </>;
}
