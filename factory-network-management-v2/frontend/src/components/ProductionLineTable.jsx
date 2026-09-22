import { useState } from 'react';
import { GlassCard } from './ui/Cards';
import Button from './ui/Button';
import DataTable from './ui/DataTable';
import SelectModeToolbar from './ui/SelectModeToolbar';
import ProductionLineStatusBadge from './ProductionLineStatusBadge';
import Icon from './ui/Icon';

const searchKeys = ['name', 'supportingInfo', 'model_names', 'vendor'];
export default function ProductionLineTable({ rows, onView, onSelectionPreview, description }) {
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState([]);
  const filters = [{ key: 'name', label: 'Production Line' }, { key: 'status', label: 'Status' }, { key: 'vendor', label: 'SW Name' }].map(filter => ({ ...filter, options: [...new Set(rows.map(row => row[filter.key]).filter(Boolean))].sort() }));
  const columns = [
    { key: 'name', label: 'Production Line', sortable: true, render: row => <div className="production-line-name"><strong>{row.name}</strong><span>{row.supportingInfo}</span></div> },
    { key: 'model_names', label: 'Model Name', sortable: true, sortValue: row => (row.model_names || []).join(' · '), render: row => <span className="production-line-vendors">{row.model_names?.length ? row.model_names.join(' · ') : '—'}</span> },
    { key: 'vendor', label: 'SW Name', sortable: true, render: row => <span className="production-line-vendors">{row.vendor || '—'}</span> },
    { key: 'total', label: 'Total Switches', sortable: true, render: row => <span className="production-line-total">{row.total}</span> },
    { key: 'status', label: 'Status', sortable: true, render: row => <ProductionLineStatusBadge status={row.status} /> },
    { key: 'action', label: 'Detail', action: true, render: row => <Button variant="ghost" aria-label={`View ${row.name}`} onClick={() => onView(row)}>View<Icon name="arrow" size={15} /></Button> },
  ];
  return <GlassCard className="table-card production-line-overview">
    <div className="table-card-header"><div><h3>Production Line Overview</h3><p className="muted">{description || `${rows.length} production lines`}</p></div></div>
    <SelectModeToolbar active={selectionMode} count={selected.length} idleText={`${rows.length} rows`} onToggle={() => { setSelectionMode(!selectionMode); setSelected([]); }}><Button disabled={!selected.length} onClick={() => onSelectionPreview(selected.length)}>Preview selection</Button></SelectModeToolbar>
    <DataTable caption="Production Line Overview" columns={columns} rows={rows} searchKeys={searchKeys} searchPlaceholder="Search production line, information or model" filterDefinitions={filters} emptyTitle="No production lines found" selectionMode={selectionMode} selected={selected} onSelectionChange={setSelected} />
    <div className="table-footnote">View stays visible. Selection is retained across pages and filters until you cancel selection.</div>
  </GlassCard>;
}
