# Sprint 0 architecture

Frontend and backend are independent. React renders the shell, plain hash navigation avoids a routing dependency, and Vite owns the development proxy. Flask uses a minimal application factory and health blueprint. No database configuration exists.

Only React and React DOM are frontend runtime dependencies. Vite, its React plugin, Tailwind and lint tooling are development dependencies. Flask is the sole direct backend dependency. Native controls, inline SVG icons and the HTML dialog element avoid UI, icon and modal libraries.

## Component contracts

- AppShell owns responsive navigation visibility. Sidebar and page layout exports live together in components/layout/AppShell.jsx.
- GlassCard wraps content; SummaryCard composes it with label, value, detail and icon props.
- Button takes primary/secondary/ghost/danger variants and standard button props.
- FormField takes label/hint/error and a render function receiving input id and ARIA attributes. Input, Select and Textarea pass through native props. Label and ValidationMessage are exported for custom fields.
- SearchInput is controlled by its consumer; it performs no search.
- StatusBadge is visual only. It expects Active, Offline or Spare.
- DataTable accepts columns (key, label, optional render/action), rows with stable id, caption and optional controlled selection. It has no fetching, sorting, pagination or mutation. Horizontal scrolling contains wide tables on small screens. A future 100-row table can use the same API; virtualization is intentionally absent.
- SelectModeToolbar is controlled by active/count/onToggle, with optional bulk-action children. Leaving select mode clears selection in the Showcase.
- ActionDropdown takes label and item objects (label, disabled, onSelect). Arrow keys, Home/End, Escape, Tab exit and outside click are supported. Primary View actions stay visible in rows.
- ConfirmDialog uses native showModal for focus containment, background inertness and Escape handling. Controlled open/onClose/onConfirm props leave decisions to the consumer. The browser restores focus to the opener.
- EmptyState takes title, description and optional action.

## Future boundaries

Business pages can replace the placeholder route definitions independently. Catalog has its own navigation entry; no image storage is invented yet. Move should become a separate action/dialog from Edit, using host-owned persistence and history in a later sprint. Import/export should belong to Inventory. Dashboard should use four summaries and a production-line table, without recent activity or additional status cards.

Sample rows live only in pages/showcase/sampleData.js. The Showcase is conditionally lazy-imported only in development, so sample JavaScript is absent from production. Showcase CSS remains lightweight shared source styling and can be removed later.

No browser storage is used. No client-side database is planned. One future LAN host owns the backend and initial SQLite database. Deployment and concurrency choices are deferred until that sprint.

## Design review

Review at 1366×768 and 1920×1080, plus narrow screens. Check information density, font hierarchy, body/Thai legibility, neutral badges, card transparency, input focus, dropdown keyboard flow, modal cancellation, visible View and selection mode. The display fallback is intentional until a licensed font file is provided.
