import { useState } from 'react';
import { GlassCard } from '../../components/ui/Cards';
import Button from '../../components/ui/Button';
import DataTable from '../../components/ui/DataTable';
import SelectModeToolbar from '../../components/ui/SelectModeToolbar';
import StatusBadge from '../../components/ui/StatusBadge';
import Icon from '../../components/ui/Icon';
import { sampleRows } from './sampleData';

const searchKeys = ['name', 'supportingInfo', 'vendor'];
const filters = [
  { key: 'name', label: 'Production Line' }, { key: 'status', label: 'Status' }, { key: 'vendor', label: 'SW Vendor' },
].map(filter => ({ ...filter, options: [...new Set(sampleRows.map(row => row[filter.key]))].sort() }));

export default function TablePreview({ onPreview }) {
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState([]);
  const columns = [
    { key: 'name', label: 'Production Line', sortable: true, render: row => <div className="production-line-name"><strong>{row.name}</strong><span>{row.supportingInfo}</span></div> },
    { key: 'vendor', label: 'SW Vendor', sortable: true, render: row => <span className="production-line-vendors">{row.vendor}</span> },
    { key: 'total', label: 'Total Switches', sortable: true, render: row => <span className="production-line-total">{row.total}</span> },
    { key: 'status', label: 'Status', sortable: true, render: row => <StatusBadge status={row.status} /> },
    { key: 'action', label: 'Detail', action: true, render: row => <Button variant="ghost" aria-label={`View ${row.name}`} onClick={() => onPreview({ title: row.name, body: `${row.supportingInfo} · ${row.vendor} · ${row.total} switches. Production line preview only; no live data is connected.` })}>View<Icon name="arrow" size={15} /></Button> },
  ];
  return <GlassCard className="table-card production-line-overview">
    <div className="table-card-header"><div><h3>Production Line Overview</h3><p className="muted">15 mock production lines · UI demonstration only</p></div></div>
    <SelectModeToolbar active={selectionMode} count={selected.length} idleText={`${sampleRows.length} sample rows`} onToggle={() => { setSelectionMode(!selectionMode); setSelected([]); }}><Button disabled={!selected.length} onClick={() => onPreview({ title: 'Selection preview', body: `${selected.length} sample row(s) selected across all pages and filters. No data will be changed.` })}>Preview selection</Button></SelectModeToolbar>
    <DataTable caption="Production Line Overview component preview" columns={columns} rows={sampleRows} searchKeys={searchKeys} searchPlaceholder="Search production line, information or model" filterDefinitions={filters} emptyTitle="No production lines found" selectionMode={selectionMode} selected={selected} onSelectionChange={setSelected} />
    <div className="table-footnote">View stays visible. Selection is retained across pages and filters until you cancel selection.</div>
  </GlassCard>;
}
