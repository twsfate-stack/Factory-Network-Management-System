import { useEffect, useId, useRef } from 'react';
import Button from './Button';

export default function ConfirmDialog({ open, title, children, onClose, onConfirm, confirmLabel = 'Confirm', cancelLabel = 'Cancel', showCancel = true, variant = 'primary', busy = false, confirmDisabled = false, className = '', headerAside, viewOnly = false }) {
  const dialog = useRef(null);
  const id = useId();
  useEffect(() => {
    const element = dialog.current;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);
  function keepFocus(event) {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]')].filter(element => element.getClientRects().length > 0);
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
  return <dialog ref={dialog} className={`modal ${className}`} aria-labelledby={`${id}-title`} aria-describedby={`${id}-body`} onKeyDown={keepFocus} onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }} onClose={() => { if (!dialog.current.open) onClose(); }}>{viewOnly ? <header className="switch-detail-header"><h2 id={`${id}-title`}>{title}</h2>{headerAside}{viewOnly && <Button variant="ghost" autoFocus onClick={onClose}>Close</Button>}</header> : <h2 id={`${id}-title`}>{title}</h2>}<div id={`${id}-body`} className={viewOnly ? "switch-detail-content" : "muted"}>{children}</div>{!viewOnly && <div className="modal-actions">{showCancel && <Button variant="secondary" autoFocus disabled={busy} onClick={onClose}>{cancelLabel}</Button>}<Button autoFocus={!showCancel} variant={variant} disabled={busy || confirmDisabled} onClick={onConfirm}>{busy ? 'Saving…' : confirmLabel}</Button></div>}</dialog>;
}
