import Icon from './Icon';
export default function EmptyState({ title = 'Nothing here yet', description, action }) {
  return <div className="empty-state"><span className="empty-icon"><Icon name="layers" size={24}/></span><h3>{title}</h3><p className="muted">{description}</p>{action}</div>;
}
