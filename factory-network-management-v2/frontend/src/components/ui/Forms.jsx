import { useId } from 'react';
import Icon from './Icon';

export function Label(props) { return <label className="label" {...props} />; }
export function ValidationMessage(props) { return <p className="field-error" role="alert" {...props} />; }
export function FormField({ label, hint, error, children, id: suppliedId }) {
  const generatedId = useId();
  const id = suppliedId || generatedId;
  return <div className="form-field"><Label htmlFor={id}>{label}</Label>{children({ id, 'aria-invalid': error ? true : undefined, 'aria-describedby': error || hint ? `${id}-message` : undefined })}{error ? <ValidationMessage id={`${id}-message`}>{error}</ValidationMessage> : hint ? <p id={`${id}-message`} className="field-hint">{hint}</p> : null}</div>;
}
export function Input({ className = '', ...props }) { return <input className={`control ${className}`} {...props} />; }
export function Select({ className = '', ...props }) { return <select className={`control ${className}`} {...props} />; }
export function Textarea({ className = '', ...props }) { return <textarea rows={3} className={`control ${className}`} {...props} />; }
export function SearchInput({ label = 'Search', className = '', ...props }) {
  return <div className={`search-input ${className}`}><Icon name="search" /><input type="search" aria-label={label} placeholder="Search hostname, model or asset ID" {...props} /></div>;
}
