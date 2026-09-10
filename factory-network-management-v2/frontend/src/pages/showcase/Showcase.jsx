import { useState } from 'react';
import TablePreview from './TablePreview';
import { PageHeader } from '../../components/layout/AppShell';
import Button from '../../components/ui/Button';
import { GlassCard, SummaryCard } from '../../components/ui/Cards';
import { FormField, Input, SearchInput, Select, Textarea } from '../../components/ui/Forms';
import StatusBadge from '../../components/ui/StatusBadge';

import ActionDropdown from '../../components/ui/ActionDropdown';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import EmptyState from '../../components/ui/EmptyState';

import Icon from '../../components/ui/Icon';


function SectionTitle({ number, title, note }) {
  return <div className="section-title"><div><span>{number}</span><h2>{title}</h2></div><p>{note}</p></div>;
}

export default function Showcase() {
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState(null);
  const [message, setMessage] = useState('All interactions on this page are local previews.');
  const announce = (label) => setMessage(`${label} preview selected. No data was changed.`);
  return <>
    <PageHeader eyebrow="DESIGN SYSTEM / 001" title="UI Showcase" description="A considered foundation for the factory floor." action={<span className="review-label"><span/>Ready for visual review</span>}/>
    <div className="showcase-note"><Icon name="layers"/><p><strong>Sprint 0 — Foundation</strong><span>Component previews only. No live factory data.</span></p><a href="#/dashboard">Explore shell <Icon name="arrow" size={16}/></a></div>
    <section aria-labelledby="visual-language"><SectionTitle number="01" title="Visual language" note="Calm surfaces. Clear hierarchy."/>
      <div className="identity-grid"><GlassCard className="type-specimen"><div className="specimen-top"><span className="eyebrow" id="visual-language">TYPOGRAPHY</span><span className="small-tag">DISPLAY / UI</span></div><p className="display-title specimen-title">FACTORY<br/>NETWORK<span className="title-period">.</span></p><div className="type-footer"><div><strong>Precision in every detail.</strong><p className="muted">Clear, readable, built for everyday work.</p><p className="thai" lang="th">ระบบจัดการเครือข่ายโรงงาน</p></div><span className="type-monogram">Aa</span></div><p className="font-note">System display fallback · SF Distant Galaxy ready</p></GlassCard>
      <GlassCard className="palette-card"><div className="specimen-top"><span className="eyebrow">CORE PALETTE</span><span className="small-tag">04 TONES</span></div><div className="palette-bars">{['background', 'surface-secondary', 'primary', 'muted'].map((token) => <div key={token} className={`swatch swatch-${token}`}/>)}</div><div className="palette-labels">{[['Background', '#F7F7F7'], ['Secondary', '#EEEEEE'], ['Primary', '#393E46'], ['Muted', '#929AAB']].map(([name, value]) => <div key={name}><strong>{name}</strong><span className="mono">{value}</span></div>)}</div><p className="muted palette-note">One neutral language, shared across every component.</p></GlassCard></div>
    </section>
    <section><SectionTitle number="02" title="Surfaces & summaries" note="Glass, with restraint."/><div className="summary-grid"><SummaryCard title="Total switches" value="—" description="Summary component preview" variant="total"/><SummaryCard title="Active" value="—" description="No live data connected" icon="check" variant="active"/><SummaryCard title="Offline" value="—" description="No live data connected" icon="clock" variant="offline"/><SummaryCard title="Spare" value="—" description="No live data connected" icon="layers" variant="spare"/></div></section>
    <section><SectionTitle number="03" title="Actions & inputs" note="Consistent by design."/><div className="controls-grid"><GlassCard className="panel"><h3>Button system</h3><p className="muted">A shared rhythm for every action.</p><div className="button-samples"><Button onClick={() => announce('Primary')}><Icon name="plus"/>Primary</Button><Button variant="secondary" onClick={() => announce('Secondary')}>Secondary</Button><Button variant="ghost" onClick={() => announce('Ghost')}>Ghost<Icon name="arrow" size={16}/></Button><Button variant="danger" onClick={() => setModal({ title: 'Danger action preview', body: 'This demonstrates confirmation styling. There is no deletion or stored data.', variant: 'danger' })}>Danger</Button><Button disabled>Disabled</Button></div><div className="panel-divider"/><div className="flex flex-wrap items-center justify-between gap-3"><div><h3>Secondary actions</h3><p className="muted">Keyboard-friendly dropdown.</p></div><ActionDropdown items={[{ label: 'Preview action', onSelect: () => announce('Dropdown') }, { label: 'Import · later sprint', disabled: true }, { label: 'Export · later sprint', disabled: true }]}/></div><div className="panel-divider"/><h3>Status vocabulary</h3><div className="flex flex-wrap gap-3 mt-4"><StatusBadge status="Active"/><StatusBadge status="Offline"/><StatusBadge status="Spare"/></div><p className="field-hint mt-3">Neutral visual variants. Status colors come later.</p></GlassCard>
      <GlassCard className="panel"><h3>Search & form controls</h3><div className="form-stack"><SearchInput value={query} onChange={(event) => setQuery(event.target.value)} aria-describedby="search-help"/><p id="search-help" className="field-hint">{query ? `Preview text: ${query}. Sample rows are not filtered.` : 'Input preview only · no search is performed.'}</p><div className="form-grid"><FormField label="Text input" hint="A short, helpful description.">{(props) => <Input {...props} placeholder="Enter a value"/>}</FormField><FormField label="Select" hint="Native keyboard interaction.">{(props) => <Select {...props} defaultValue=""><option value="" disabled>Choose an option</option><option>Sample option A</option><option>Sample option B</option></Select>}</FormField></div><FormField label="Notes">{(props) => <Textarea {...props} placeholder="Add a short note…"/>}</FormField><FormField label="Validation example" error="Enter a value to continue. (Sample message)">{(props) => <Input {...props} placeholder="Required value"/>}</FormField></div></GlassCard></div></section>
    <section><SectionTitle number="04" title="Table & selection" note="Useful information, without the clutter."/><TablePreview onPreview={setModal}/></section>
    <section><SectionTitle number="05" title="Feedback & overlays" note="Clear, focused decisions."/><div className="controls-grid"><GlassCard><EmptyState title="A clean starting point" description="Empty states make the next step clear, without adding noise."/></GlassCard><GlassCard className="panel overlay-preview"><span className="empty-icon"><Icon name="layers" size={24}/></span><h3>A moment to confirm</h3><p className="muted">Focused dialogs with keyboard support and a clear way back.</p><Button variant="secondary" onClick={() => setModal({ title: 'Confirm preview', body: 'Review this dialog’s spacing, focus and buttons. Confirming only updates the preview message.' })}>Open dialog<Icon name="arrow" size={16}/></Button></GlassCard></div></section>
    <p className="preview-message" role="status">{message}</p><ConfirmDialog open={Boolean(modal)} title={modal?.title || 'Preview'} variant={modal?.variant} onClose={() => setModal(null)} onConfirm={() => { setModal(null); announce('Confirmation'); }} confirmLabel="Confirm preview">{modal?.body}</ConfirmDialog>
  </>;
}
