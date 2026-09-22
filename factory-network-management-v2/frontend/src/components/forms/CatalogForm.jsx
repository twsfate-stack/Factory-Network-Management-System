import { useEffect, useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import { FormField, Input, Textarea } from '../ui/Forms';
import CatalogImage from '../CatalogImage';
import Button from '../ui/Button';
import { api } from '../../services/api';

export default function CatalogForm({ entry = null, onClose, onSaved }) {
  const form = useRef(null);
  const picker = useRef(null);
  const pending = useRef(false);
  const [file, setFile] = useState(null);
  const [removed, setRemoved] = useState(false);
  const [preview, setPreview] = useState(null);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  function choose(event) {
    const selected = event.target.files[0];
    event.target.value = '';
    if (!selected) return;
    if (!/\.(jpe?g|png|webp)$/i.test(selected.name)) { setError('Unsupported image format. Use JPG, PNG or WEBP.'); return; }
    if (selected.size > 5 * 1024 * 1024) { setError('Image must be 5 MB or smaller.'); return; }
    setPreview(URL.createObjectURL(selected)); setFile(selected); setRemoved(false); setError('');
  }
  function removeImage() { setFile(null); setPreview(null); setRemoved(true); }

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true); setError('');
    const data = new FormData(form.current);
    if (file) data.set('image', file);
    else if (removed) data.set('remove_image', 'true');
    try { await (entry ? api.editCatalog(entry.id, data) : api.addCatalog(data)); }
    catch (failure) { pending.current = false; setBusy(false); setError(failure.message); return; }
    onSaved();
  }
  return <ConfirmDialog open title={entry ? 'Edit Switch Model' : 'Add Switch Model'} onClose={onClose} onConfirm={() => form.current.requestSubmit()} confirmLabel={busy ? 'Saving...' : entry ? 'Save Changes' : 'Add Model'} busy={busy}>
    <form ref={form} onSubmit={submit} className="form-stack">
      {error && <p role="alert" className="field-error">{error}</p>}
      <div className="form-stack">
        <span className="label">Switch Image</span>
        <CatalogImage url={file ? preview : removed ? null : entry?.image_url} name={entry?.name || 'Switch model'} />
        {file && <p className="muted break-words">{file.name}</p>}
        <input ref={picker} type="file" accept=".jpg,.jpeg,.png,.webp" aria-label="Choose Switch Image" hidden onChange={choose} disabled={busy} />
        <div className="flex gap-2"><Button variant="secondary" disabled={busy} onClick={() => picker.current.click()}>{file || (!removed && entry?.image_url) ? 'Change Image' : 'Upload Image'}</Button>{(file || (!removed && entry?.image_url)) && <Button variant="ghost" disabled={busy} onClick={removeImage}>Remove Image</Button>}</div>
        <p className="muted">JPG / PNG / WEBP. Max 5 MB.</p>
      </div>
      {[['name', 'Model Name', 251], ['vendor', 'Vendor', 100], ['model', 'Model', 150]].map(([name, label, maxLength]) => <FormField key={name} label={label}>{props => <Input {...props} name={name} required maxLength={maxLength} defaultValue={entry?.[name] || ''} disabled={busy} />}</FormField>)}
      <FormField label="Description (optional)">{props => <Textarea {...props} name="description" maxLength={2000} defaultValue={entry?.description || ''} disabled={busy} />}</FormField>
      <button type="submit" hidden />
    </form>
  </ConfirmDialog>;
}
