import { useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Select, Textarea } from '../ui/Forms';
import { api } from '../../services/api';

export default function MoveSwitch({ record, lines, onClose, onSaved }) {
  const form = useRef(null);
  const saving = useRef(false);
  const [values, setValues] = useState({ production_line_id: '', block: '', hostname: '', notes: '' });
  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const destination = lines.find(line => line.id === Number(values.production_line_id));
  const comparisons = [['Production Line', record.production_line, destination?.name], ['Block', record.block, values.block], ['Hostname', record.hostname, values.hostname]];
  function change(event) { setValues(previous => ({ ...previous, [event.target.name]: event.target.value })); }
  function continueMove(event) {
    event.preventDefault();
    const next = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value.trim()]));
    if (!destination || !next.hostname) { setError('Select a Production Line and enter a Hostname.'); return; }
    if (destination.id === record.production_line_id && next.hostname === record.hostname && next.block === (record.block || '')) { setError('No changes to move.'); return; }
    setValues(next); setError(''); setReview(true);
  }
  async function confirmMove() {
    if (saving.current) return;
    saving.current = true; setBusy(true); setError('');
    try {
      await api.moveSwitch(record.id, { ...values, production_line_id: destination.id, expected_updated_at: record.updated_at });
    } catch (failure) {
      setError(failure.message); saving.current = false; setBusy(false); return;
    }
    onSaved();
  }
  return <ConfirmDialog open title={review ? 'Review Move' : 'Move Switch'} busy={busy}
    onClose={() => { if (review) { setReview(false); setError(''); } else onClose(); }}
    cancelLabel={review ? 'Back' : 'Cancel'} confirmLabel={review ? 'Confirm Move' : 'Continue'}
    onConfirm={() => review ? confirmMove() : form.current.requestSubmit()}>
    <div className="move-identity"><strong>{record.hostname}</strong><p>{record.vendor} {record.model}</p><p>Asset ID: {record.asset_id || '—'} · Serial Number: {record.serial_number || '—'}</p></div>
    {error && <p className="field-error" role="alert">{error}</p>}
    {review ? <div className="move-review">
      <div className="move-comparison"><span /><strong>FROM</strong><strong>TO</strong></div>
      {comparisons.map(([label, from, to]) => <div className="move-comparison" key={label}><span>{label}</span><span>{from || '—'}</span><strong>{to || '—'}</strong></div>)}
      {values.notes && <p className="move-note">Note: {values.notes}</p>}
    </div> : <>
      <div className="move-current"><h3>CURRENT LOCATION</h3><dl>{[['Production Line', record.production_line], ['Block', record.block], ['Hostname', record.hostname]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value || '—'}</dd></div>)}</dl></div>
      <form ref={form} className="form-stack" onSubmit={continueMove}>
        <h3 className="move-section-title">MOVE TO</h3>
        <FormField label="Production Line">{props => <Select {...props} name="production_line_id" required value={values.production_line_id} onChange={change}><option value="">Select Production Line</option>{lines.map(line => <option key={line.id} value={line.id}>{line.name}</option>)}</Select>}</FormField>
        <FormField label="Block (optional)">{props => <Input {...props} name="block" maxLength={100} value={values.block} onChange={change} />}</FormField>
        <FormField label="Hostname">{props => <Input {...props} name="hostname" required maxLength={150} value={values.hostname} onChange={change} />}</FormField>
        <FormField label="Reason / Note (optional)">{props => <Textarea {...props} name="notes" maxLength={4000} value={values.notes} onChange={change} />}</FormField>
        <button type="submit" hidden />
      </form>
    </>}
  </ConfirmDialog>;
}
