export default function SortHeader({ column, direction, onSort }) {
  return <th scope="col" aria-sort={column.sortable ? direction || 'none' : undefined} className={column.action ? 'action-column' : ''}>
    {column.sortable ? <button type="button" className="table-sort" onClick={onSort} aria-label={`Sort by ${column.label}: ${!direction ? 'ascending' : direction === 'ascending' ? 'descending' : 'default order'}`}>
      {column.label}<span className="table-sort-indicator" aria-hidden="true">{direction === 'ascending' ? '↑' : direction === 'descending' ? '↓' : ''}</span>
    </button> : column.label}
  </th>;
}
