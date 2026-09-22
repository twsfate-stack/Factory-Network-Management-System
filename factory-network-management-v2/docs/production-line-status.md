# Production Line operational status

GET /api/production-lines now returns derived status WORKING, NOT WORKING or NO SWITCH. With only non-deleted related records: zero total means NO SWITCH; at least one ACTIVE means WORKING; otherwise NOT WORKING. OFFLINE and SPARE Switches never override a remaining ACTIVE Switch. No schema or stored value changes were needed.

Switch.status, its allowed ACTIVE/OFFLINE/SPARE values, the inline Inventory dropdown/API, dates and soft-delete/PIN behavior remain unchanged. Dashboard summary cards still count individual Switch statuses. Production Line View continues fetching non-deleted Switch records with each real status.

The Production Line table uses a separate ProductionLineStatusBadge with existing pill CSS and existing green/orange/neutral tokens. The shared Switch StatusBadge is unchanged. Line filter values reflect the new backend terms. Showcase line fixtures also use the new vocabulary.

Following an inline change, backend calculations use the saved Switch statuses. Opening Dashboard/Production Lines fetches fresh derived information automatically without a manual browser reload, following the current navigation data flow. Independent tabs do not receive push updates.

Created: frontend/src/components/ProductionLineStatusBadge.jsx and docs/production-line-status.md.
Modified: backend/app/routes/production_lines.py, backend/tests/test_data.py, backend/tests/test_security.py, frontend/src/components/ProductionLineTable.jsx, frontend/src/pages/showcase/sampleData.js and docs/data-foundation.md.

Validation: 35 backend tests, lint and production build passed. Cases include ACTIVE+OFFLINE, ACTIVE+SPARE, OFFLINE-only, OFFLINE+SPARE, SPARE-only, empty, 3 ACTIVE/2 OFFLINE/1 SPARE, 5 OFFLINE/1 SPARE and deleted ACTIVE exclusion. Existing inline status, Dashboard counting, persistence, soft-delete and restore tests also pass. Browser verification showed NO SWITCH for an empty line, WORKING for ACTIVE/OFFLINE/SPARE, real individual Switch statuses in View, and WORKING -> NOT WORKING -> WORKING after inline changes with correct Switch summary counts and unchanged total. All test records were isolated from the live database.
