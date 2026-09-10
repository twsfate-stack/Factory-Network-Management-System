import { PageHeader } from '../components/layout/AppShell';
import { GlassCard } from '../components/ui/Cards';
import EmptyState from '../components/ui/EmptyState';

export default function Placeholder({ page }) {
  return <><PageHeader eyebrow="WORKSPACE / FOUNDATION" title={page.title} description="The workspace is ready for the next sprint."/><GlassCard><EmptyState title={`${page.label} is planned`} description="Sprint 0 establishes the layout and components. This section has no business features yet." action={import.meta.env.DEV ? <a href="#/showcase" className="button button-primary">Open UI Showcase</a> : undefined}/></GlassCard></>;
}
