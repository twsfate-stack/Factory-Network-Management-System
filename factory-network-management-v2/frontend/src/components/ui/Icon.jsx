const paths = {
  grid: 'M3 3h6v6H3z M15 3h6v6h-6z M3 15h6v6H3z M15 15h6v6h-6z',
  server: 'M3 4h18v6H3z M3 14h18v6H3z M6 7h1 M6 17h1 M11 7h7 M11 17h7',
  layers: 'm12 3 10 5-10 5L2 8z M2 12l10 5 10-5 M2 16l10 5 10-5',
  network: 'M9 2h6v6H9z M2 16h6v6H2z M16 16h6v6h-6z M12 8v4 M5 16v-4h14v4',
  clock: 'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  settings: 'M9.5 2h5l.5 2.5 2 1.2 2.4-.8 2.5 4.2-1.9 1.7v2.4l1.9 1.7-2.5 4.2-2.4-.8-2 1.2-.5 2.5h-5L9 19.5l-2-1.2-2.4.8-2.5-4.2L4 13.2v-2.4l-1.9-1.7 2.5-4.2 2.4.8 2-1.2z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6',
  arrow: 'M5 12h14 M14 7l5 5-5 5', chevron: 'm7 10 5 5 5-5', plus: 'M12 5v14 M5 12h14',
  close: 'm6 6 12 12 M6 18 18 6', menu: 'M4 6h16 M4 12h16 M4 18h16', check: 'm5 12 4 4L19 6',
};
export default function Icon({ name, size = 18, ...props }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}><path d={paths[name] || paths.grid} /></svg>;
}
