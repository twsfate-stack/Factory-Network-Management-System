import { useMemo, useState } from 'react';
import EmptyState from './EmptyState';
import Button from './Button';
import SortHeader from './SortHeader';
import Pagination from './Pagination';
import TableFilters from './TableFilters';
import { getTableRows } from './tableData';

const EMPTY = [];
export default function DataTable({ columns, rows, caption, searchKeys = EMPTY, searchPlaceholder, filterDefinitions = EMPTY, emptyTitle = 'No results found', emptyDescription = 'Try changing your search or filters.', selectionMode = false, selected = EMPTY, onSelectionChange, filterActions, selectAllVisible = false, clearSelectionOnViewChange = false, onCriteriaChange }) {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [sort, setSort] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const results = useMemo(() => getTableRows(rows, { query, searchKeys, filters, sort, columns }), [rows, query, searchKeys, filters, sort, columns]);
  const currentPage = Math.min(page, Math.max(1, Math.ceil(results.length / pageSize)));
  const visibleRows = results.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const hasFilters = searchKeys.length > 0 || filterDefinitions.length > 0;
  const clearSelection = () => { if (clearSelectionOnViewChange && selectionMode) onSelectionChange?.([]); };
  function resetFilters() { clearSelection(); setQuery(''); setFilters({}); setPage(1); onCriteriaChange?.({ query: '', filters: {} }); }
  function changeSort(key) {
    clearSelection();
    setSort(previous => previous?.key !== key ? { key, direction: 'ascending' } : previous.direction === 'ascending' ? { key, direction: 'descending' } : null);
    setPage(1);
  }
  const toggle = id => onSelectionChange?.(selected.includes(id) ? selected.filter(value => value !== id) : [...selected, id]);
  return <div className="data-table">
    {hasFilters && <TableFilters query={query} searchPlaceholder={searchPlaceholder} searchEnabled={searchKeys.length > 0} onQueryChange={value => { clearSelection(); setQuery(value); setPage(1); onCriteriaChange?.({ query: value, filters }); }} definitions={filterDefinitions} values={filters} onFilterChange={(key, value) => { clearSelection(); setFilters(previous => ({ ...previous, [key]: value })); setPage(1); onCriteriaChange?.({ query, filters: { ...filters, [key]: value } }); }} onReset={resetFilters} actions={filterActions} />}
    <div className="table-scroll" tabIndex={0} role="region" aria-label={caption}><table>
      <caption className="sr-only">{caption}</caption>
      <thead><tr>{selectionMode && <th scope="col">{selectAllVisible ? <input type="checkbox" aria-label="Select all visible models" disabled={!visibleRows.length} checked={visibleRows.length > 0 && visibleRows.every(row => selected.includes(row.id))} ref={element => { if (element) element.indeterminate = visibleRows.some(row => selected.includes(row.id)) && !visibleRows.every(row => selected.includes(row.id)); }} onChange={event => onSelectionChange?.(event.target.checked ? [...new Set([...selected, ...visibleRows.map(row => row.id)])] : selected.filter(id => !visibleRows.some(row => row.id === id)))} /> : <span className="sr-only">Select row</span>}</th>}{columns.map(column => <SortHeader key={column.key} column={column} direction={sort?.key === column.key ? sort.direction : undefined} onSort={() => changeSort(column.key)} />)}</tr></thead>
      <tbody>{visibleRows.length ? visibleRows.map(row => <tr key={row.id} className={selectionMode && selected.includes(row.id) ? 'is-selected' : ''}>
        {selectionMode && <td><input type="checkbox" aria-label={`Select ${row.name || row.hostname || row.id}`} checked={selected.includes(row.id)} onChange={() => toggle(row.id)} /></td>}
        {columns.map(column => <td key={column.key} className={column.action ? 'action-column' : ''}>{column.render ? column.render(row) : row[column.key]}</td>)}
      </tr>) : <tr><td colSpan={columns.length + Number(selectionMode)}><EmptyState title={emptyTitle} description={emptyDescription} action={hasFilters ? <Button variant="secondary" onClick={resetFilters}>Reset filters</Button> : undefined} /></td></tr>}</tbody>
    </table></div>
    <Pagination page={currentPage} pageSize={pageSize} total={results.length} onPageChange={value => { clearSelection(); setPage(value); }} onPageSizeChange={size => { clearSelection(); setPageSize(size); setPage(1); }} />
  </div>;
}
