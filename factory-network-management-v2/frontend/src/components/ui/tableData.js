const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
export function getTableRows(rows, { query = '', searchKeys = [], filters = {}, sort = null, columns = [] } = {}) {
  const needle = query.trim().toLocaleLowerCase();
  const result = rows.filter(row => (!needle || searchKeys.some(key => String(row[key] ?? '').toLocaleLowerCase().includes(needle))) && Object.entries(filters).every(([key, value]) => !value || String(row[key] ?? '') === value));
  const column = columns.find(item => item.key === sort?.key);
  if (!column || !sort) return result;
  const value = column.sortValue || (row => row[column.key]);
  return result.sort((a, b) => {
    const left = value(a), right = value(b);
    const compared = typeof left === 'number' && typeof right === 'number' ? left - right : collator.compare(String(left ?? ''), String(right ?? ''));
    return sort.direction === 'ascending' ? compared : -compared;
  });
}
