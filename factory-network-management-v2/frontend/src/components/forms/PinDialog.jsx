import { useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input } from '../ui/Forms';

export default function PinDialog({ mode, count, onClose, onSubmit, onSaved }) {
  const form = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const deleting = mode === 'delete';
  const fields = deleting ? [['pin', '6-digit Delete PIN']] : [...(mode === 'change' ? [['current_pin', 'Current PIN']] : []), ['new_pin', 'New PIN'], ['confirm_pin', 'Confirm PIN']];
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const values = Object.fromEntries(new FormData(form.current));
    setBusy(true); setError('');
    try { await onSubmit(values); }
    catch (failure) { form.current.reset(); setError(failure.message); setBusy(false); return; }
    form.current.reset(); onSaved();
  }
  return <ConfirmDialog open title={deleting ? `Delete ${count} ${count === 1 ? 'switch' : 'switches'}?` : mode === 'change' ? 'Change Delete PIN' : 'Set Delete PIN'} onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel={deleting ? 'Confirm Delete' : 'Save PIN'} variant={deleting ? 'danger' : 'primary'} busy={busy}>
    {deleting && <p>These switches will be removed from the active inventory but can be restored later.</p>}
    <form ref={form} onSubmit={submit} className="form-stack">
      {error && <p role="alert" className="field-error">{error}</p>}
      {fields.map(([name, label]) => <FormField key={name} label={label}>{props => <Input {...props} name={name} type="password" inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} required autoComplete={name === 'new_pin' || name === 'confirm_pin' ? 'new-password' : 'off'} disabled={busy} />}</FormField>)}
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
