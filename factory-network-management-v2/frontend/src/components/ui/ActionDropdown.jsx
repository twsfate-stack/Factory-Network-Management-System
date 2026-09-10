import { useEffect, useId, useRef, useState } from 'react';
import Button from './Button';
import Icon from './Icon';

export default function ActionDropdown({ label = 'Actions', items }) {
  const [open, setOpen] = useState(false);
  const root = useRef(null);
  const trigger = useRef(null);
  const id = useId();
  useEffect(() => {
    if (!open) return;
    const close = (event) => { if (!root.current?.contains(event.target)) setOpen(false); };
    document.addEventListener('pointerdown', close);
    root.current.querySelector('[role="menuitem"]:not(:disabled)')?.focus();
    return () => document.removeEventListener('pointerdown', close);
  }, [open]);
  function keyDown(event) {
    if (event.key === 'Escape') { setOpen(false); trigger.current.focus(); }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const options = [...root.current.querySelectorAll('[role="menuitem"]:not(:disabled)')];
      const index = options.indexOf(document.activeElement);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? options.length - 1 : (index + (event.key === 'ArrowUp' ? -1 : 1) + options.length) % options.length;
      options[next]?.focus();
    }
  }
  return <div className="dropdown" ref={root} onKeyDown={keyDown} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}><Button ref={trigger} variant="secondary" aria-haspopup="menu" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)} onKeyDown={(event) => { if (event.key === 'ArrowDown' && !open) { event.preventDefault(); setOpen(true); } }}>{label}<Icon name="chevron" /></Button>{open && <div id={id} className="dropdown-menu" role="menu" aria-label={label}>{items.map((item) => <button type="button" key={item.label} role="menuitem" disabled={item.disabled} onClick={() => { setOpen(false); trigger.current.focus(); item.onSelect?.(); }}>{item.label}</button>)}</div>}</div>;
}
