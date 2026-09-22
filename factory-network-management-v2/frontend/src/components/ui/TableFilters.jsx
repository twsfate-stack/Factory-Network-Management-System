import { SearchInput, Select } from './Forms';
import Button from './Button';
export default function TableFilters({ query, onQueryChange, searchEnabled, searchPlaceholder = 'Search hostname, model or asset ID', definitions, values, onFilterChange, onReset, actions }) {
  return <div className="table-filters" role="search" aria-label="Table filters">
    {searchEnabled && <label className="table-search"><span>Search</span><SearchInput label="Search table" placeholder={searchPlaceholder} value={query} onChange={event => onQueryChange(event.target.value)} /></label>}
    {definitions.map(filter => <label key={filter.key}><span>{filter.label}</span><Select aria-label={filter.label} value={values[filter.key] || ''} onChange={event => onFilterChange(filter.key, event.target.value)}><option value="">All {filter.label.toLowerCase()}</option>{filter.options.map(option => <option key={option} value={option}>{option}</option>)}</Select></label>)}
    {actions}
    <Button variant="secondary" onClick={onReset}>Reset</Button>
  </div>;
}
