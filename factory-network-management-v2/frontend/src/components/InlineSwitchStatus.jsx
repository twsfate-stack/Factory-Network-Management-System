import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import StatusBadge from './ui/StatusBadge';
import { api } from '../services/api';

const statuses = ['ACTIVE', 'OFFLINE', 'SPARE'];
export default function InlineSwitchStatus({ row, onSaved }) {
  const trigger = useRef(null);
  const menu = useRef(null);
  const saving = useRef(false);
  const [position, setPosition] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const id = useId();
  function open() {
    if (saving.current) return;
    const rect = trigger.current.getBoundingClientRect();
    setPosition({ left: Math.max(8, Math.min(rect.left, window.innerWidth - 168)), top: rect.bottom + 7, above: window.innerHeight - rect.bottom < 180, bottom: window.innerHeight - rect.top + 7 });
  }
  useEffect(() => {
    if (!position) return;
    menu.current?.querySelector('[aria-checked="true"]')?.focus();
    const outside = event => { if (!trigger.current?.contains(event.target) && !menu.current?.contains(event.target)) setPosition(null); };
    const close = () => setPosition(null);
    document.addEventListener('pointerdown', outside);
    window.addEventListener('resize', close);
    window.addEventListener('scroll', close, true);
    return () => { document.removeEventListener('pointerdown', outside); window.removeEventListener('resize', close); window.removeEventListener('scroll', close, true); };
  }, [position]);
  async function choose(status) {
    setPosition(null); trigger.current?.focus();
    if (status === row.status || saving.current) return;
    saving.current = true; setBusy(true); setError('');
    try { const result = await api.updateSwitchStatus(row.id, status); onSaved(result.data); }
    catch { setError('Unable to update switch status. Please try again.'); }
    finally { saving.current = false; setBusy(false); }
  }
  function menuKey(event) {
    if (event.key === 'Escape') { event.preventDefault(); setPosition(null); trigger.current?.focus(); }
    if (event.key === 'Tab') { setPosition(null); trigger.current?.focus(); }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const options = [...menu.current.querySelectorAll('button')];
      const index = options.indexOf(document.activeElement);
      options[event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (index + (event.key === 'ArrowUp' ? -1 : 1) + 3) % 3]?.focus();
    }
  }
  return <>
    <button ref={trigger} type="button" disabled={busy} aria-busy={busy} aria-label={`Change status for ${row.hostname}: ${row.status}`} aria-haspopup="menu" aria-expanded={Boolean(position)} aria-controls={position ? id : undefined} style={{ border: 0, padding: 0, background: 'transparent', opacity: busy ? 0.6 : 1, cursor: busy ? 'wait' : 'pointer' }} onClick={() => position ? setPosition(null) : open()} onKeyDown={event => { if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); open(); } }}><StatusBadge status={row.status} /></button>
    {error && <p role="alert" className="field-error">{error}</p>}
    {position && createPortal(<div ref={menu} id={id} role="menu" aria-label={`Status for ${row.hostname}`} className="dropdown-menu" style={{ position: 'fixed', left: position.left, right: 'auto', top: position.above ? 'auto' : position.top, bottom: position.above ? position.bottom : 'auto', width: 160, zIndex: 100 }} onKeyDown={menuKey} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setPosition(null); }}>
      {statuses.map(status => <button key={status} type="button" role="menuitemradio" aria-checked={row.status === status} onClick={() => choose(status)}><span aria-hidden="true" style={{ display: 'inline-block', width: 20 }}>{row.status === status ? '✓' : ''}</span><StatusBadge status={status} /></button>)}
    </div>, document.body)}
  </>;
}
