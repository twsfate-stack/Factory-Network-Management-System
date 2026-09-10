import { GlassShineCard } from './glass-shine-card';

export function GlassCard({ children, className = '', ...props }) {
  return <div className={`glass-card ${className}`} {...props}>{children}</div>;
}
export function SummaryCard({ title, value, description, variant = 'total' }) {
  return <GlassShineCard className="summary-card" data-variant={variant}>
    <div className="summary-label"><span>{title}</span></div>
    <strong className="summary-value">{value}</strong>
    {description && <p className="muted">{description}</p>}
  </GlassShineCard>;
}
