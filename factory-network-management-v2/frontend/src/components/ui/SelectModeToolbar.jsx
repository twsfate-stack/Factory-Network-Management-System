import Button from './Button';
export default function SelectModeToolbar({ active, count, onToggle, children, idleText = 'Select rows to preview bulk actions' }) {
  return <div className="selection-toolbar"><span className="muted" aria-live="polite">{active ? `${count} selected` : idleText}</span><div className="flex flex-wrap items-center gap-2">{active && children}<Button variant="secondary" onClick={onToggle}>{active ? 'Cancel selection' : 'Select'}</Button></div></div>;
}
