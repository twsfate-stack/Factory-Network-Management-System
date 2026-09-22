import { useEffect, useRef, useState } from 'react';
import ConfirmDialog from '../ui/ConfirmDialog';
import Button from '../ui/Button';
import { FormField, Input } from '../ui/Forms';
import { api } from '../../services/api';

export default function DeleteCatalogs({ ids, onClose, onSaved }) {
  const form = useRef(null);
  const pending = useRef(false);
  const [review, setReview] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([api.previewCatalogDelete(ids), api.pinStatus()]).then(([result, pin]) => {
      if (active) { setReview({ ...result, ...pin }); setError(''); }
    }).catch(failure => { if (active) setError(failure.message); });
    return () => { active = false; };
  }, [ids, attempt]);
  async function submit(event) {
    event.preventDefault();
    if (pending.current || !review?.eligible.length || !review.pin_configured) return;
    pending.current = true; setBusy(true); setError('');
    const pin = new FormData(form.current).get('pin');
    try {
      // Only send models explicitly reviewed as eligible, never newly eligible blocked rows.
      const result = await api.deleteCatalogs({ ids: review.eligible.map(row => row.id), pin });
      form.current.reset();
      onSaved({ ...result, blocked: [...review.blocked, ...result.blocked] });
    } catch (failure) { form.current?.reset(); setError(failure.message); setBusy(false); pending.current = false; }
  }
  const canDelete = Boolean(review?.eligible.length && review.pin_configured);
  return <ConfirmDialog open title="Delete Switch Models" onClose={onClose} busy={busy} variant={canDelete ? 'danger' : 'secondary'}
    showCancel={canDelete} confirmLabel={canDelete ? `Delete ${review.eligible.length} Models` : 'Close'} confirmDisabled={!review && !error}
    onConfirm={() => canDelete ? form.current.requestSubmit() : onClose()}>
    {!review && !error && <p role="status">Checking current switch references…</p>}
    {error && <p role="alert" className="field-error">{error}</p>}
    {!review && error && <Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry review</Button>}
    {review && <div className="form-stack">
      <p>{review.eligible.length ? `${review.eligible.length} models can be deleted permanently.` : 'Cannot delete selected models.'}</p>
      {review.eligible.length > 0 && <div><h3 className="label">CAN DELETE</h3><ul>{review.eligible.map(row => <li className="break-words" key={row.id}>{row.name}</li>)}</ul></div>}
      {review.blocked.length > 0 && <div><h3 className="label">CANNOT DELETE</h3><ul>{review.blocked.map(row => <li className="mb-2 break-words" key={row.id}><strong>{row.name}</strong><p>{row.reason}</p></li>)}</ul></div>}
      <p>Only models with no physical Switch references can be deleted. Switches in Recycle Bin also protect their models.</p>
      {review.eligible.length > 0 && (review.pin_configured ? <form ref={form} className="form-stack" onSubmit={submit}>
        <FormField label="6-digit Delete PIN">{props => <Input {...props} name="pin" type="password" inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} required autoComplete="off" disabled={busy} />}</FormField>
        <button type="submit" hidden />
      </form> : <p role="alert">Delete PIN is not configured. Set a 6-digit Delete PIN in <a href="/#/settings">Settings</a> before deleting models.</p>)}
    </div>}
  </ConfirmDialog>;
}
