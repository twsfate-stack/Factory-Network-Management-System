import { useEffect, useId, useRef } from 'react';
import Button from './Button';

export default function ConfirmDialog({ open, title, children, onClose, onConfirm, confirmLabel = 'Confirm', variant = 'primary' }) {
  const dialog = useRef(null);
  const id = useId();
  useEffect(() => {
    const element = dialog.current;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);
  function keepFocus(event) {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]')];
    const first = controls[0];
    const last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  }
  return <dialog ref={dialog} className="modal" aria-labelledby={`${id}-title`} aria-describedby={`${id}-body`} onKeyDown={keepFocus} onCancel={(event) => { event.preventDefault(); onClose(); }} onClose={() => { if (!dialog.current.open) onClose(); }}><h2 id={`${id}-title`}>{title}</h2><div id={`${id}-body`} className="muted">{children}</div><div className="modal-actions"><Button variant="secondary" autoFocus onClick={onClose}>Cancel</Button><Button variant={variant} onClick={onConfirm}>{confirmLabel}</Button></div></dialog>;
}
