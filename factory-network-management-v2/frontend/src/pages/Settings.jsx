import { useEffect, useState } from 'react';
import { PageHeader } from '../components/layout/AppShell';
import { GlassCard } from '../components/ui/Cards';
import Button from '../components/ui/Button';
import PinDialog from '../components/forms/PinDialog';
import { api } from '../services/api';

export default function Settings() {
  const [configured, setConfigured] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [editing, setEditing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    api.pinStatus().then(data => { if (active) { setConfigured(data.pin_configured); setError(''); } }).catch(failure => { if (active) setError(failure.message); });
    return () => { active = false; };
  }, [attempt]);
  return <>
    <PageHeader eyebrow="WORKSPACE / FOUNDATION" title="Settings" description="The workspace is ready for the next sprint." />
    <GlassCard className="panel"><h3>Delete Security</h3>
      {message && <p role="status" className="preview-message">{message}</p>}
      {error ? <><p role="alert">{error}</p><Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry</Button></> : <>
        <p className="muted mb-4">{configured === null ? 'Loading Delete Security…' : configured ? 'Delete PIN configured' : 'Delete PIN not configured'}</p>
        <Button disabled={configured === null} onClick={() => setEditing(true)}>{configured ? 'Change PIN' : 'Set Delete PIN'}</Button>
      </>}
    </GlassCard>
    {editing && <PinDialog mode={configured ? 'change' : 'setup'} onClose={() => setEditing(false)} onSubmit={configured ? api.changePin : api.setupPin} onSaved={() => { setEditing(false); setConfigured(true); setMessage(configured ? 'Delete PIN updated successfully.' : 'Delete PIN configured.'); }} />}
  </>;
}
