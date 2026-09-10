import { useState } from 'react';
import { navigation } from '../../config/navigation';
import Icon from '../ui/Icon';
import Button from '../ui/Button';

export function Sidebar({ route, open, onClose }) {
  return <><button type="button" className={`sidebar-scrim ${open ? 'visible' : ''}`} aria-label="Close navigation" onClick={onClose} /><aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Main navigation"><a className="brand" href="#/dashboard" onClick={onClose}><span>FACTORY<br/><strong>NETWORK</strong></span></a><div className="sidebar-caption">WORKSPACE <span>V2</span></div><nav>{navigation.map((item) => <a key={item.id} href={`#/${item.id}`} className={`nav-link ${route === item.id ? 'active' : ''}`} aria-current={route === item.id ? 'page' : undefined} onClick={onClose}><Icon name={item.icon} /><span>{item.label}</span>{route === item.id && <span className="nav-indicator" />}</a>)}</nav><div className="sidebar-footer"><span className="foundation-mark"/><div><strong>Clean rebuild</strong><p>Sprint 0 · Foundation</p></div><span className="version">0.1</span></div></aside></>;
}
export function PageContainer({ children }) { return <main id="main-content" className="page-container" tabIndex={-1}>{children}</main>; }
export function PageHeader({ eyebrow, title, description, action }) {
  return <header className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1 className="display-title">{title}</h1>{description && <p className="page-description">{description}</p>}</div>{action}</header>;
}
export default function AppShell({ route, children }) {
  const [open, setOpen] = useState(false);
  const current = navigation.find((item) => item.id === route);
  return <div className="app-shell"><a href="#main-content" className="skip-link" onClick={(event) => { event.preventDefault(); document.getElementById('main-content').focus(); }}>Skip to content</a><Sidebar route={route} open={open} onClose={() => setOpen(false)} /><div className="workspace"><div className="topbar"><div className="flex items-center gap-3"><Button variant="ghost" className="mobile-menu" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} onClick={() => setOpen(!open)}><Icon name={open ? 'close' : 'menu'} /></Button><span className="breadcrumb">Workspace <span>/</span> <strong>{current?.label || 'UI Showcase'}</strong></span></div><span className="preview-pill">FOUNDATION PREVIEW</span></div><PageContainer>{children}</PageContainer><footer className="workspace-footer"><span>FACTORY NETWORK MANAGEMENT SYSTEM</span><span>V2 / SPRINT 0</span></footer></div></div>;
}
