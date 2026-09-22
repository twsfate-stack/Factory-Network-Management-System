import { useId, useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import Button from '../ui/Button';
import { FormField, Select } from '../ui/Forms';
import DataTable from '../ui/DataTable';
import { api } from '../../services/api';

const columns = [
  { key: 'row', label: 'Row' }, { key: 'hostname', label: 'Hostname' },
  { key: 'serial_number', label: 'Serial Number' }, { key: 'switch_model', label: 'Switch Model' },
  { key: 'production_line', label: 'Production Line' }, { key: 'normalized_status', label: 'Status' },
  { key: 'result', label: 'Result', render: row => <div><strong>{row.result}</strong>{row.errors.map(error => <p className="field-error" key={error}>{error}</p>)}</div> },
];

export default function InventoryTransfer({ mode, criteria, onClose, onImported }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [scope, setScope] = useState('all');
  const [format, setFormat] = useState('xlsx');
  const pending = useRef(false);
  const fileInput = useRef(null);
  const fileInputId = useId();
  const importing = mode === 'import';
  async function run(action) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError('');
    try { await action(); }
    catch (failure) { setError(failure.message); }
    finally { pending.current = false; setBusy(false); }
  }
  function choose(event) {
    const selected = event.target.files[0];
    setPreview(null); setError(''); setFile(null);
    if (!selected) return;
    if (!selected.name.toLowerCase().endsWith('.csv')) { setError('Choose a CSV UTF-8 file.'); return; }
    if (selected.size > 5 * 1024 * 1024) { setError('Import file must be 5 MB or smaller.'); return; }
    setFile(selected);
  }
  async function confirm() {
    if (!importing) return run(async () => { await api.exportInventory(scope, criteria, format); onClose(); });
    if (!preview || preview.errors || !file) return;
    return run(async () => {
      try { const result = await api.confirmImport(file, preview.fingerprint); onImported(result.imported_count); }
      catch (failure) { setPreview(null); throw failure; }
    });
  }
  return <ConfirmDialog open title={importing ? 'Import Switch Inventory' : 'Export Switch Inventory'}
    className={importing && preview ? 'inventory-import-modal' : ''} busy={busy} onClose={onClose} onConfirm={confirm}
    confirmLabel={importing ? 'Confirm Import' : format === 'xlsx' ? 'Download Excel' : 'Download CSV'} confirmDisabled={importing && (!preview || preview.errors > 0)}>
    <div className="form-stack">
      {error && <p role="alert" className="field-error">{error}</p>}
      {importing ? <>
        <p>Use existing Switch Catalog model names and Production Line names. CSV UTF-8, maximum 5 MB / 5,000 rows.</p>
        <div><Button variant="secondary" disabled={busy} onClick={() => run(api.importTemplate)}>Download Template</Button></div>
        <div className="inventory-file-field">
          <label className="label" htmlFor={fileInputId}>Choose File</label>
          <input id={fileInputId} ref={fileInput} type="file" accept=".csv,text/csv" hidden disabled={busy} onChange={choose} />
          <button type="button" className="inventory-file-picker" disabled={busy} aria-controls={fileInputId} onClick={() => fileInput.current.click()}>
            <strong>{file ? file.name : 'Choose CSV File'}</strong>
            <span>{file ? `${(file.size / 1024).toLocaleString(undefined, { maximumFractionDigits: 1 })} KB` : 'CSV file up to 5 MB'}</span>
            {file && <span>Click to choose another file</span>}
          </button>
        </div>
        <div><Button variant="secondary" disabled={busy || !file} onClick={() => run(async () => { setPreview(null); setPreview(await api.previewImport(file)); })}>Validate &amp; Preview</Button></div>
        {busy && <p role="status">Processing file, please wait...</p>}
        {preview && <>
          <h3>IMPORT PREVIEW</h3>
          <p role="status">Total Rows: {preview.total} · Valid: {preview.valid} · Errors: {preview.errors}</p>
          <p>{preview.errors ? 'No rows will be imported. Correct the file and validate again.' : `${preview.valid} Switches are ready to import.`}</p>
          <DataTable caption="Import preview" columns={columns} rows={preview.rows.map(row => ({ ...row, id: row.row }))} />
        </>}
      </> : <>
        <FormField label="Export Format">{props => <Select {...props} value={format} disabled={busy} onChange={event => setFormat(event.target.value)}><option value="xlsx">Excel (.xlsx)</option><option value="csv">CSV</option></Select>}</FormField>
        <p>{format === 'xlsx' ? 'Excel includes Switch Inventory and all Move History for the exported switches. Dates use Thailand time.' : 'CSV UTF-8 includes current Switch Inventory only.'} Recycle Bin records are excluded.</p>
        <label><input type="radio" name="export-scope" value="all" checked={scope === 'all'} disabled={busy} onChange={() => setScope('all')} /> Export All</label>
        <label><input type="radio" name="export-scope" value="current" checked={scope === 'current'} disabled={busy} onChange={() => setScope('current')} /> Export Current Results</label>
        <p>Current Results includes every row matching the current search and filters, across all pages.</p>
      </>}
    </div>
  </ConfirmDialog>;
}
