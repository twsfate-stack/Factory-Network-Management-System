export function GlassShineCard({ children, className = '', ...props }) {
  return <div className={`glass-shine-card ${className}`} {...props}>
    <div className="glass-shine-card__content">{children}</div>
  </div>;
}
