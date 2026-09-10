export default function StatusBadge({ status }) {
  return <span className={`status-badge status-${status.toLowerCase()}`}><span aria-hidden="true" />{status.toUpperCase()}</span>;
}
