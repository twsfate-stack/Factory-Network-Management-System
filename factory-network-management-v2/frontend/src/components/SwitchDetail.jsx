import CatalogImage from './CatalogImage';
import { useEffect, useState } from 'react';
import ConfirmDialog from './ui/ConfirmDialog';
import StatusBadge from './ui/StatusBadge';
import Button from './ui/Button';
import { api, passportPath } from '../services/api';
import RecordDate from './RecordDate';

const sections = [
  ['BASIC INFORMATION', [['hostname', 'Hostname'], ['serial_number', 'Serial Number'], ['asset_id', 'Asset ID']]],
  ['DEVICE', [['vendor', 'Vendor'], ['model', 'Model'], ['firmware_version', 'Firmware']]],
  ['NETWORK', [['ip_address', 'IP Address'], ['mac_address', 'MAC Address']]],
  ['LOCATION', [['production_line', 'Production Line'], ['block', 'Block']]],
];
export default function SwitchDetail({ switchId, onClose }) {
  const [record, setRecord] = useState(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    api.switch(switchId).then(data => { if (active) { setRecord(data); setError(''); } }).catch(failure => { if (active) setError(failure.message); });
    return () => { active = false; };
  }, [switchId, attempt]);
  return <ConfirmDialog open title={record?.hostname || 'Switch details'} onClose={onClose} viewOnly className="switch-detail-modal" headerAside={record && <StatusBadge status={record.status} />}>
    {error ? <div><p role="alert">{error}</p><Button variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry</Button></div> : !record ? <p role="status">Loading switch…</p> : <>
      {record.catalog_image_url && <CatalogImage url={record.catalog_image_url} name={record.catalog_name || record.model} />}
      <div className="switch-detail-grid">
        {sections.map(([title, fields]) => <section className="switch-detail-section" key={title} aria-label={title}>
          <h3>{title}</h3>
          <dl>{fields.map(([key, label]) => <div className="switch-detail-row" key={key}><dt>{label}</dt><dd>{record[key] || '—'}</dd></div>)}</dl>
        </section>)}
      </div>
      <section className="switch-detail-notes" aria-label="Notes"><h3>NOTES</h3><p>{record.notes || '—'}</p></section>
      {record.passport_uid && <a className="button button-secondary mb-4" href={passportPath(record.passport_uid)}>View Passport / QR</a>}
      <dl className="switch-detail-dates">{[['created_at', 'Created Date'], ['updated_at', 'Updated Date']].map(([key, label]) => <div key={key}><dt>{label}</dt><dd><RecordDate value={record[key]} /></dd></div>)}</dl>
    </>}
  </ConfirmDialog>;
}
