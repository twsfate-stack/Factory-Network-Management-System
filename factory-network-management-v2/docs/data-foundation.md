# Sprint 1 — Data foundation

This milestone adds real SQLite storage and Dashboard data flow while retaining the approved Sprint 0 components. The development Showcase remains available with isolated mock data; it is not the live Dashboard.

## Database

Default file: `backend/data/factory_network.db`, resolved relative to backend source, independent of the working directory. Flask creates the directory and tables on first run. It never seeds, resets or drops real data. To move storage, set the `FACTORY_DATABASE_PATH` environment variable to an absolute path before starting Flask.

| Table | Columns |
| --- | --- |
| production_lines | id, name (unique, required), description, created_at, updated_at |
| switches | id, hostname (required), asset_id (optional unique), serial_number (optional unique), vendor (required), model (required), production_line_id (required foreign key), status, ip_address (optional unique), mac_address, firmware_version, notes, created_at, updated_at |

Timestamps are UTC ISO strings in API responses. Names/IDs are trimmed. Blank optional values become NULL, so multiple records can omit identifiers. Line names, asset IDs and serial numbers use SQLite NOCASE uniqueness (ASCII case-insensitive). IP addresses are parsed and normalized before uniqueness checking. Foreign keys and a five-second busy timeout are enabled. SQL constraints protect concurrent duplicate writes as well as application validation.

Back up the database separately from source: stop Flask, then copy `backend/data/factory_network.db`. Preserve this file during application updates. Git ignores database files and test artifacts. Do not delete it to apply updates. Automatic `create_all` creates missing tables only; future schema changes require an explicit migration plan. No migration system is included yet.

## API

| Method | Endpoint | Response |
| --- | --- | --- |
| GET | /api/health | Existing status/application object |
| POST | /api/production-lines | 201: {success: true, data: line summary} |
| GET | /api/production-lines | Array of stored lines with description, totals, status and unique switch_models |
| POST | /api/switches | 201: {success: true, data: saved switch} |
| GET | /api/switches | Array of saved switches |
| GET | /api/dashboard | {total_switches, active, offline, spare} |

Switch list filters: `production_line` (numeric ID), `status` (ACTIVE/OFFLINE/SPARE), `vendor` (exact), `search` (case-insensitive literal substring in hostname, asset ID or model). Filters combine with AND; matching search fields combine with OR.

Validation failures return HTTP 400 and `{success: false, message: "Readable explanation"}`. Duplicate fields are named in the message; raw SQLAlchemy errors are not returned. A storage failure returns a generic HTTP 503 message. Invalid/non-object JSON and oversized requests are rejected.

Create line payload: `{ "name": "S27", "description": "bondi ag" }`.

Create switch payload:

```json
{
  "hostname": "SW-S27-001",
  "vendor": "Arista",
  "model": "7060",
  "production_line_id": 1,
  "status": "ACTIVE"
}
```

Asset ID, serial number, IP address, MAC address, firmware_version and notes are optional. Production Line must already exist. Hostname is intentionally not unique in this milestone; asset/serial/IP identify duplicate inventory when supplied.

## Calculations and UI flow

Dashboard counts are calculated by a database GROUP BY on switch status; total is their sum. No hardcoded counts or browser persistence are used.

Line summaries are calculated once on the backend using eagerly loaded assigned switches. Each line returns total quantity and a deduplicated, alphabetically sorted list of `vendor + model` combinations.

Line status precedence:

1. Any OFFLINE switch → OFFLINE.
2. Otherwise any ACTIVE switch → ACTIVE (including mixed active/spare lines).
3. Otherwise a nonempty all-SPARE line → SPARE.
4. Empty line → null; the UI displays “No switches,” not an invented operational status.

Dashboard and Production Lines navigation use the same live table. Dashboard also shows the approved four summary cards. Add Production Line is available from both. Add Switch is enabled after a line exists. Save commits to SQLite, closes the form, and reloads Dashboard counts and line summaries. If saving fails, the form stays open with entered values. If refresh fails after a successful save, a saved notice remains and Retry is available; resubmission is not requested.

View requests actual switches filtered by line ID and presents hostname, vendor/model and StatusBadge in a simple modal. Selection remains UI-only; no bulk mutation is implemented.

## Frontend service configuration

All request URLs live in `frontend/src/services/api.js`. The provided `.env.example` defaults to `VITE_API_BASE_URL=/api`. The development proxy in vite.config.js forwards to `http://127.0.0.1:5050`. This avoids CORS and hardcoded factory IPs. For deployment, keep a same-origin `/api` reverse proxy; cross-origin API hosting is not configured in this milestone. Vite environment changes require a restart/rebuild.

## Tests and boundaries

13 unittest tests pass: file/table creation, restart persistence, line creation/uniqueness, switch creation, empty defaults, all status counts, line aggregation/deduplication/status, optional values, duplicate asset/serial/normalized IP, validation, query filters and health.

Browser acceptance checks use a separate SQLite file under ignored `artifacts/`: zero counts → create S27 → add SW-S27-001 → total/active/line count 1; View; duplicate validation; OFFLINE and SPARE additions; reload persistence; backend failure and Retry; 1366, 1920 and 390px layouts. The normal database is left empty for the user's real entries.

No auth, roles, edit/delete, QR, history storage, import/export, monitoring, topology, deployment stack or live multi-user push updates. Another browser's writes appear after reopening/reloading the live page. Requests use bounded timeouts; no background polling is added. A lost connection during saving can leave the outcome uncertain; check stored records before retrying.

The server is loopback-only Flask development mode, not a production LAN server. Dependencies require internet or a prefilled package cache for installation. SQLite is appropriate for this first small local milestone; cross-host hosting and operational backups need a later deployment pass.

## Files introduced/changed

- Backend: app/models.py, app/validation.py, app/routes/{dashboard,production_lines,switches}.py, app/__init__.py, tests/test_data.py, tests/test_health.py, requirements.txt, requirements.lock.txt, data/README.md.
- Frontend: services/api.js, pages/Dashboard.jsx, components/ProductionLineTable.jsx, components/forms/{AddProductionLine,AddSwitch}.jsx, App.jsx, ui/ConfirmDialog.jsx, pages/showcase/TablePreview.jsx, .env.example.
- Documentation/config: README.md, docs/data-foundation.md, .gitignore.
- Approved theme CSS, cards, glass shine, shadows, StatusBadge, SearchInput, sidebar branding and gear are unchanged from the checkpoint.
