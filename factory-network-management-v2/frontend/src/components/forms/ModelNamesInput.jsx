import { useId, useState } from 'react';
import { Input } from '../ui/Forms';
import Button from '../ui/Button';

export default function ModelNamesInput({ values, onChange, draft, onDraftChange, disabled }) {
  const id = useId();
  const [error, setError] = useState('');
  function add() {
    const name = draft.trim();
    if (!name) return;
    if (values.some(value => value.toLocaleLowerCase() === name.toLocaleLowerCase())) { setError('This Model Name is already added.'); return; }
    if (values.length >= 50) { setError('Use up to 50 Model Names.'); return; }
    onChange([...values, name]); onDraftChange(''); setError('');
  }
  return <div className="form-stack">
    <label className="label" htmlFor={id}>Model Name</label>
    <div className="flex items-center gap-2"><Input id={id} value={draft} onChange={event => { onDraftChange(event.target.value); setError(''); }} maxLength={150} disabled={disabled} placeholder="Enter model name" aria-describedby={error ? `${id}-error` : undefined} aria-invalid={Boolean(error)} onKeyDown={event => { if (event.key === 'Enter') { event.preventDefault(); add(); } }} /><Button type="button" variant="secondary" disabled={disabled || !draft.trim()} onClick={add}>+ Add</Button></div>
    {error && <p id={`${id}-error`} role="alert" className="field-error">{error}</p>}
    <div className="flex flex-wrap gap-2">{values.map(name => <span key={name} className="inline-flex items-center gap-2" style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-pill)', background: 'var(--background)', padding: '4px 9px' }}>{name}<button type="button" disabled={disabled} aria-label={`Remove ${name}`} onClick={() => { onChange(values.filter(value => value !== name)); setError(''); }} style={{ border: 0, background: 'transparent', padding: '0 3px' }}>×</button></span>)}</div>
  </div>;
}
