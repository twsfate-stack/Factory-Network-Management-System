import CatalogImage from '../components/CatalogImage';
import { useEffect, useState } from 'react';
import Button from '../components/ui/Button';
import StatusBadge from '../components/ui/StatusBadge';
import RecordDate from '../components/RecordDate';
import { api } from '../services/api';
import '../styles/passport.css';
import { navigation } from '../config/navigation';

function Fields({ title, fields, record, className = '' }) {
  return <section className={`passport-section ${className}`} aria-label={title}><h2>{title}</h2><dl>{fields.map(([key, label]) => <div className="passport-field" key={key}><dt>{label}</dt><dd>{record[key] || '—'}</dd></div>)}</dl></section>;
}
const location = [['production_line', 'Production Line'], ['block', 'Block'], ['hostname', 'Hostname']];
const identity = [['asset_id', 'Asset ID'], ['serial_number', 'Serial Number'], ['vendor', 'Vendor'], ['model', 'Model'], ['firmware_version', 'Firmware']];
const network = [['ip_address', 'IP Address'], ['mac_address', 'MAC Address']];
const position = (entry, prefix) => [entry[`${prefix}_production_line_name`], entry[`${prefix}_block`] || '—', entry[`${prefix}_hostname`]].join(' / ');

function goBack() {
  const isSystemPage = value => {
    if (!value) return false;
    try {
      const url = new URL(value);
      return url.origin === window.location.origin && url.pathname === '/' &&
        (!url.hash || navigation.some(page => url.hash === `#/${page.id}`));
    } catch { return false; }
  };
  // Navigation entries retain the previous hash route even after a Passport reload.
  const browserNavigation = window.navigation;
  const previous = browserNavigation?.entries().find(entry => entry.index === browserNavigation.currentEntry.index - 1);
  const canGoBack = browserNavigation
    ? isSystemPage(previous?.url)
    : window.history.length > 1 && isSystemPage(document.referrer);
  if (canGoBack) window.history.back();
  else window.location.replace('/#/dashboard');
}

export default function Passport({ uid }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [qrReady, setQrReady] = useState(false);
  const [qrError, setQrError] = useState(false);
  useEffect(() => {
    let active = true;
    let pending = false;
    async function refresh() {
      if (pending) return;
      pending = true;
      try { const result = await api.passport(uid); if (active) { setData(result); setError(''); } }
      catch (failure) { if (active) setError(failure.message); }
      finally { pending = false; }
    }
    const visibleRefresh = () => { if (!document.hidden) refresh(); };
    refresh();
    const timer = setInterval(visibleRefresh, 30000);
    window.addEventListener('focus', visibleRefresh);
    document.addEventListener('visibilitychange', visibleRefresh);
    return () => { active = false; clearInterval(timer); window.removeEventListener('focus', visibleRefresh); document.removeEventListener('visibilitychange', visibleRefresh); };
  }, [uid, attempt]);
  const record = data?.switch;
  return <main className="passport-page">
    <header className="passport-header passport-screen"><a href="/#/inventory" className="passport-home">FNMS</a><div><Button variant="ghost" onClick={goBack}>← Back</Button></div><p className="passport-eyebrow">SWITCH PASSPORT</p>
      {record?.catalog_image_url && <CatalogImage url={record.catalog_image_url} name={record.catalog_name || record.model} />}
      {record && <><div className="passport-title"><h1>{record.hostname}</h1><StatusBadge status={record.status} /></div><p>{record.vendor} {record.model}</p></>}
    </header>
    {error && <div className="passport-section passport-screen"><p role="alert">{error}</p>{data && <p>Displayed information may be out of date.</p>}<Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry</Button></div>}
    {!data && !error && <p className="passport-screen" role="status">Loading Switch Passport…</p>}
    {record && <>
      {record.is_deleted && <div className="passport-archived passport-screen" role="status"><strong>SWITCH NOT ACTIVE IN INVENTORY</strong><p>This Switch is currently archived / deleted. Its Passport identity is preserved.</p><p>Deleted: <RecordDate value={record.deleted_at} /></p></div>}
      <div className="passport-details passport-screen">
        <Fields title="CURRENT LOCATION" fields={location} record={record} className="passport-location" />
        <Fields title="DEVICE IDENTITY" fields={identity} record={record} className="passport-identity" />
        <Fields title="NETWORK INFORMATION" fields={network} record={record} />
        <section className="passport-section" aria-label="Notes"><h2>NOTES</h2><p className="passport-notes">{record.notes || '—'}</p></section>
      </div>
      <section className="passport-section passport-screen" aria-label="History"><h2>HISTORY</h2>
        {data.history.length ? <ol className="passport-history">{data.history.map((entry, index) => <li key={`${entry.moved_at}-${index}`}><RecordDate value={entry.moved_at} /><h3>MOVE SWITCH</h3><p>{position(entry, 'from')}</p><p aria-label="Moved to">↓</p><p>{position(entry, 'to')}</p>{entry.notes && <p className="passport-notes muted">{entry.notes}</p>}</li>)}</ol> : <p className="muted">No moves recorded for this switch.</p>}
        {data.has_more_history && <p className="muted">Showing the 10 most recent moves.</p>}
        <div className="passport-created"><h3>ADDED TO SYSTEM</h3><RecordDate value={record.created_at} /><p className="muted">Updated: <RecordDate value={record.updated_at} /> · Thailand time (UTC+7)</p></div>
      </section>
      <section className="passport-section passport-qr-section" aria-label="QR Code"><h2 className="passport-screen">QR CODE</h2>
        {data.passport_url ? <>
          <div className="passport-label"><strong>QMB FNMS</strong><img key={data.passport_url} src={api.passportQr(uid)} alt="QR code linking to this permanent Switch Passport" onLoad={() => { setQrReady(data.passport_url); setQrError(false); }} onError={() => { setQrReady(false); setQrError(true); }} /><p>Asset ID: {record.asset_id || '—'}</p><p>SN: {record.serial_number || '—'}</p><small>{data.passport_uid}</small></div>
          {qrError && <p role="alert" className="passport-screen">Unable to load the QR code. Reload the Passport to try again.</p>}
          <p className="passport-url passport-screen"><a href={data.passport_url}>{data.passport_url}</a></p>
          <div className="passport-actions passport-screen"><Button disabled={qrReady !== data.passport_url} onClick={() => window.print()}>Print QR Label</Button>{qrReady === data.passport_url && <a className="button button-secondary" href={`${api.passportQr(uid)}?download=1`} download={`FNMS_${uid}_QR.png`}>Download QR</a>}</div>
          <p className="muted passport-screen">Use factory Wi-Fi or a network that can reach FNMS. Before printing, confirm this address is the permanent factory address. Turn off browser print headers and footers.</p>
        </> : <p className="passport-screen">QR printing is unavailable until the server’s PUBLIC_BASE_URL is configured with a stable factory address.</p>}
      </section>
    </>}
  </main>;
}
