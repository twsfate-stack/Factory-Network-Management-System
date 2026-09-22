import { useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Textarea } from '../ui/Forms';
import { api } from '../../services/api';
import ModelNamesInput from './ModelNamesInput';

export default function AddProductionLine({ line = null, onClose, onSaved }) {
  const form = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [modelNames, setModelNames] = useState(line?.model_names || []);
  const [draft, setDraft] = useState('');
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const names = draft.trim() ? [...modelNames, draft.trim()] : modelNames;
    const values = { ...Object.fromEntries(new FormData(form.current)), model_names: names };
    setBusy(true); setError('');
    try {
      await (line ? api.editProductionLine(line.id, values) : api.addProductionLine(values));
    } catch (failure) { setError(failure.message); setBusy(false); return; }
    onSaved(line ? 'Production Line updated.' : 'Production Line added.');
  }
  return <ConfirmDialog open title={line ? "Edit Production Line" : "Add Production Line"} onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel={line ? "Save Changes" : "Save Production Line"} busy={busy}>
    <form ref={form} onSubmit={submit} className="form-stack">
      {error && <p role="alert" className="field-error">{error}</p>}
      <FormField label="Production Line name">{props => <Input {...props} name="name" defaultValue={line?.name || ''} required maxLength={100} placeholder="S27" disabled={busy} />}</FormField>
      <ModelNamesInput values={modelNames} onChange={setModelNames} draft={draft} onDraftChange={setDraft} disabled={busy} />
      <FormField label="Description (optional)">{props => <Textarea {...props} name="description" defaultValue={line?.description || ''} maxLength={500} placeholder="bondi ag" disabled={busy} />}</FormField>
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
