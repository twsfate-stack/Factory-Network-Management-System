import { useEffect, useRef, useState } from 'react';
import Button from '../ui/Button';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Select, Textarea } from '../ui/Forms';
import { api } from '../../services/api';

export default function AddSwitch({ lines, onClose, onSaved, record = null }) {
  const form = useRef(null);
  const [catalogId, setCatalogId] = useState(String(record?.catalog_id || ''));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [catalogs, setCatalogs] = useState(null);
  const chosen = catalogs?.find(row => String(row.id) === catalogId);
  const [catalogError, setCatalogError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    api.catalogs().then(rows => { if (active) { setCatalogs(rows); setCatalogError(''); } })
      .catch(failure => { if (active) setCatalogError(failure.message); });
    return () => { active = false; };
  }, [attempt]);
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (!catalogs?.length) { setError('Add a Switch Model in Switch Catalog before saving.'); return; }
    const data = Object.fromEntries(new FormData(form.current));
    if (record) { delete data.production_line_id; delete data.block; }
    else data.production_line_id = Number(data.production_line_id);
    data.catalog_id = Number(data.catalog_id);
    setBusy(true); setError('');
    try { if (record) await api.editSwitch(record.id, data); else await api.addSwitch(data); }
    catch (failure) { setError(failure.message); setBusy(false); return; }
    onSaved(record ? 'Switch updated.' : 'Switch added.');
  }
  const field = (name, label, required = false, maximum = 150) => <FormField key={name} label={label}>{props => <Input {...props} name={name} defaultValue={record?.[name] || ''} readOnly={Boolean(record && name === 'block')} required={required} maxLength={maximum} disabled={busy} />}</FormField>;
  return <ConfirmDialog open title={record ? "Edit Switch" : "Add Switch"} onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel={record ? "Save Changes" : "Save Switch"} confirmDisabled={!catalogs?.length || Boolean(catalogError)} busy={busy}>
    <form ref={form} className="form-stack" onSubmit={submit}>
      {error && <p role="alert" className="field-error">{error}</p>}
      {field('hostname', 'Hostname', true)}
      {field('serial_number', 'Serial Number (optional)')}
      {catalogError ? <div><p role="alert" className="field-error">{catalogError}</p><Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry models</Button></div> : !catalogs ? <p role="status">Loading switch models…</p> : !catalogs.length ? <p>No switch models found. <a href="/#/catalog">Add a model in Switch Catalog.</a></p> : null}
      <FormField label="Switch Model">{props => <Select {...props} name="catalog_id" required value={catalogId} onChange={event => setCatalogId(event.target.value)} disabled={busy || !catalogs?.length}><option value="" disabled>Select Switch Model</option>{catalogs?.map(catalog => <option key={catalog.id} value={catalog.id}>{catalog.name} - {catalog.vendor} / {catalog.model}</option>)}</Select>}</FormField>
      {chosen && <dl className="form-grid"><div><dt className="label">Vendor</dt><dd>{chosen.vendor}</dd></div><div><dt className="label">Model</dt><dd>{chosen.model}</dd></div></dl>}
      {record && !record.catalog_id && <p className="muted">Catalog model not assigned. Existing device: {record.vendor} / {record.model}. Select the correct model.</p>}
      {record && <p className="muted">Use Move Switch to change Production Line or Block.</p>}
      <div className="form-grid">
        <FormField label="Production Line">{props => <Select {...props} name="production_line_id" required defaultValue={record?.production_line_id || ""} disabled={busy || Boolean(record)}><option value="" disabled>Select a line</option>{lines.map(line => <option key={line.id} value={line.id}>{line.name}</option>)}</Select>}</FormField>
        <FormField label="Status">{props => <Select {...props} name="status" defaultValue={record?.status || "ACTIVE"} disabled={busy}>{['ACTIVE', 'OFFLINE', 'SPARE'].map(status => <option key={status}>{status}</option>)}</Select>}</FormField>
      </div>
      {field('block', 'Block (optional)', false, 100)}
      <details><summary>More details (optional)</summary><div className="form-stack">
        {field('asset_id', 'Asset ID')}{field('ip_address', 'IP Address', false, 45)}{field('mac_address', 'MAC Address', false, 50)}{field('firmware_version', 'Firmware')}
        <FormField label="Notes">{props => <Textarea {...props} name="notes" defaultValue={record?.notes || ""} maxLength={4000} disabled={busy} />}</FormField>
      </div></details>
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
