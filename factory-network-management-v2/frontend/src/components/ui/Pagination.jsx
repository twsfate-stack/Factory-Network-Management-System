import Button from './Button';
import { Select } from './Forms';
export default function Pagination({ page, pageSize, total, onPageChange, onPageSizeChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return <div className="table-pagination">
    <span className="muted" role="status">Showing {total ? (page - 1) * pageSize + 1 : 0}–{Math.min(page * pageSize, total)} of {total}</span>
    <label className="table-page-size">Rows per page<Select aria-label="Rows per page" value={pageSize} onChange={event => onPageSizeChange(Number(event.target.value))}>{[10, 25, 50].map(size => <option key={size} value={size}>{size}</option>)}</Select></label>
    <nav aria-label="Table pagination"><Button variant="ghost" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Previous</Button><span aria-current="page">Page {page} of {pages}</span><Button variant="ghost" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>Next</Button></nav>
  </div>;
}
