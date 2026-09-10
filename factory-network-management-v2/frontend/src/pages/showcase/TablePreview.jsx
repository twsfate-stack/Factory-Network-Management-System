import ProductionLineTable from '../../components/ProductionLineTable';
import { sampleRows } from './sampleData';

export default function TablePreview({ onPreview }) {
  return <ProductionLineTable rows={sampleRows} description="15 mock production lines · UI demonstration only" onView={row => onPreview({ title: row.name, body: `${row.supportingInfo} · ${row.vendor} · ${row.total} switches. Production line preview only; no live data is connected.` })} onSelectionPreview={count => onPreview({ title: 'Selection preview', body: `${count} sample row(s) selected across all pages and filters. No data will be changed.` })} />;
}