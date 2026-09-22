const variants = { WORKING: 'active', 'NOT WORKING': 'offline', 'NO SWITCH': 'neutral' };

export default function ProductionLineStatusBadge({ status = 'NO SWITCH' }) {
  const label = Object.hasOwn(variants, status) ? status : 'NO SWITCH';
  return <span className={`status-badge status-${variants[label]}`}><span aria-hidden="true" />{label}</span>;
}
