import { useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Select, Textarea } from '../ui/Forms';
import { api } from '../../services/api';

export default function AddSwitch({ lines, onClose, onSaved }) {
  const form = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const data = Object.fromEntries(new FormData(form.current));
    data.production_line_id = Number(data.production_line_id);
    setBusy(true); setError('');
    try { await api.addSwitch(data); }
    catch (failure) { setError(failure.message); setBusy(false); return; }
    onSaved('Switch added.');
  }
  const field = (name, label, required = false, maximum = 150) => <FormField key={name} label={label}>{props => <Input {...props} name={name} required={required} maxLength={maximum} disabled={busy} />}</FormField>;
  return <ConfirmDialog open title="Add Switch" onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel="Save Switch" busy={busy}>
    <form ref={form} className="form-stack" onSubmit={submit}>
      {error && <p role="alert" className="field-error">{error}</p>}
      {field('hostname', 'Hostname', true)}
      {field('serial_number', 'Serial Number (optional)')}
      <div className="form-grid">{field('vendor', 'Vendor', true, 100)}{field('model', 'Model', true)}</div>
      <div className="form-grid">
        <FormField label="Production Line">{props => <Select {...props} name="production_line_id" required defaultValue="" disabled={busy}><option value="" disabled>Select a line</option>{lines.map(line => <option key={line.id} value={line.id}>{line.name}</option>)}</Select>}</FormField>
        <FormField label="Status">{props => <Select {...props} name="status" defaultValue="ACTIVE" disabled={busy}>{['ACTIVE', 'OFFLINE', 'SPARE'].map(status => <option key={status}>{status}</option>)}</Select>}</FormField>
      </div>
      <details><summary>More details (optional)</summary><div className="form-stack">
        {field('asset_id', 'Asset ID')}{field('ip_address', 'IP Address', false, 45)}{field('mac_address', 'MAC Address', false, 50)}{field('firmware_version', 'Firmware')}
        <FormField label="Notes">{props => <Textarea {...props} name="notes" maxLength={4000} disabled={busy} />}</FormField>
      </div></details>
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
