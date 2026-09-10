import { useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Textarea } from '../ui/Forms';
import { api } from '../../services/api';

export default function AddProductionLine({ onClose, onSaved }) {
  const form = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError('');
    try {
      await api.addProductionLine(Object.fromEntries(new FormData(form.current)));
    } catch (failure) { setError(failure.message); setBusy(false); return; }
    onSaved('Production Line added.');
  }
  return <ConfirmDialog open title="Add Production Line" onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel="Save Production Line" busy={busy}>
    <form ref={form} onSubmit={submit} className="form-stack">
      {error && <p role="alert" className="field-error">{error}</p>}
      <FormField label="Production Line name">{props => <Input {...props} name="name" required maxLength={100} placeholder="S27" disabled={busy} />}</FormField>
      <FormField label="Description (optional)">{props => <Textarea {...props} name="description" maxLength={500} placeholder="bondi ag" disabled={busy} />}</FormField>
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
