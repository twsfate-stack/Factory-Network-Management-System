# Switch Inventory + Block + Thailand Created Date

Inventory uses real SQLite records and the approved reusable DataTable, SearchInput, filters, badges and buttons. Dashboard source and styling remain unchanged.

## Storage and safety

The persistent database is backend/data/factory_network.db. Switches have a required production_line_id foreign key; quantities and vendor/model summaries are derived from records, never manually stored on a Production Line.

Block is nullable VARCHAR(100). Input is trimmed; blank values become NULL and values exceeding 100 characters return validation errors. No values are hardcoded.

Startup app/schema.py performs an idempotent additive SQLite upgrade under a write transaction. It adds missing Block and timestamp columns without recreating tables. Missing legacy creation dates use upgrade time (SQLite CURRENT_TIMESTAMP, UTC), not a recovered historical creation time. Missing updated_at uses created_at. Known timestamps, existing rows, indexes and relationships are preserved. Pre-Block and pre-dates SQLite backups are in backend/data and ignored by Git. This Thailand revision requires no additional schema changes or timestamp rewrites.

## Centralized Thailand time

backend/app/timezone.py uses zoneinfo.ZoneInfo("Asia/Bangkok"). tzdata==2025.2 is pinned in both requirement files to supply IANA timezone data on Windows. Normal runtime requires no internet.

SQLAlchemy generates created_at from the backend UTC clock at insert. updated_at has an automatic ORM update default. Client payloads cannot override either timestamp. SQLite DATETIME values remain UTC, preserving existing moments. API serialization converts them to ISO 8601 with +07:00 for Switch and Production Line responses.

Example: database 2026-09-10 17:16:32 UTC -> API 2026-09-11T00:16:32+07:00 -> UI 2026-09-11 00:16.

The shared frontend RecordDate component uses Intl.DateTimeFormat with Asia/Bangkok, independent of browser timezone. Inventory and View consistently display YYYY-MM-DD HH:mm. The API retains seconds and microseconds. Sorting uses the full timestamp. No manual seven-hour arithmetic is used.

## Inventory and shared form

The eleven columns are Hostname, Serial Number, Asset ID, Vendor / Model, IP Address, Production Line, Block, Firmware, Status, Created Date, Actions. View is directly accessible and displays all fields including MAC, Notes, Created Date and Updated Date.

Dashboard and Inventory use the same components/forms/AddSwitch.jsx and api.addSwitch method. Production Line options come from the database. Block is a main optional input; dates have no editable form fields. Saving refreshes the current page; navigation automatically fetches updated Dashboard/line totals and Inventory records without a browser reload or Flask restart.

Search matches hostname, serial, asset, vendor, model, IP, Production Line and Block. Production Line, Status and Vendor filters, sorting, pagination (10/25/50), empty state and selection compatibility reuse DataTable. Optional blank values display an em dash without storing one.

## APIs

- GET /api/switches: real records and basic query filters.
- POST /api/switches: saves and returns the record with timezone-aware dates.
- GET /api/switches/:id: fresh record or readable 404.
- GET and POST /api/production-lines: stored lines and derived summaries.
- GET /api/dashboard: Switch counts by status.
- GET /api/health: backend health.

Use firmware_version in writes; responses retain that name and provide firmware as an alias.

## Files

Inventory milestone created backend/app/schema.py, frontend/src/pages/SwitchInventory.jsx, frontend/src/components/SwitchDetail.jsx, frontend/src/components/RecordDate.jsx and this document. It modified backend initialization, models, Switch routes and tests, frontend App routing, API service, shared AddSwitch and README. Existing relationship audit changes were preserved.

Thailand revision created backend/app/timezone.py and modified backend/app/models.py, backend/app/routes/production_lines.py, backend/requirements.txt, backend/requirements.lock.txt, backend/tests/test_data.py and this document. No frontend code or design changes were necessary for this revision.

## Validation

21 backend tests pass: creation, persistence, validation/duplicates, Block/serial, detail, search, derived counts/aggregation, foreign key safety, timestamp generation/client override prevention, update behavior, legacy migration preservation/idempotence and explicit timezone conversion. Frontend lint and production build pass using pnpm.

Browser acceptance against an isolated real SQLite backend passed A10 creation and both SW-A10-001 (SN001234, AT001, Arista 7060, 172.16.10.21, B01, 4.32.1F) and SW-A10-002 (SN001235, Quanta LYB, B02), both ACTIVE. Counts became 1 then 2. Search, vendor filter/reset, View, persistence and responsive widths 1366/1920/390 passed without JavaScript errors.

A fixed UTC database instant at 2026-09-10 17:16:32 was verified as +07:00 API time and 2026-09-11 00:16 in Inventory and View, even with the browser timezone set to America/Los_Angeles. User records were not used for test inserts.

## Limitations

Narrow screens horizontally scroll the eleven-column table. Client-side filtering targets a few hundred records. No cross-tab push updates or edit endpoint are introduced. Direct external SQL edits do not invoke the ORM updated_at default. QR, history, move, repair, delete, authentication, monitoring and import/export remain outside scope.
