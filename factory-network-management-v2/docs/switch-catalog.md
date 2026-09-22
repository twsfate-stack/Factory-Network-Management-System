# Switch Catalog master data

## Structure and source of truth

SwitchCatalog (switch_catalog) contains id, name, vendor, model, description, created_at and updated_at, plus normalized vendor_key/model_key for a database-enforced composite unique constraint. Keys trim/collapse whitespace and casefold Unicode; display values retain their spelling. Model Name is a friendly Catalog name, separate from Production Line model_names.

Switch.catalog_id references switch_catalog.id and has an index. The existing vendor/model columns are retained as legacy compatibility snapshots; they are never rewritten when a Catalog is edited. API serialization uses Catalog vendor/model/name whenever linked, falling back to the legacy values only for an unlinked record. Inventory, Switch View, Move identity display and Passport therefore use the same source. Passport IDs, physical identity, Move History and Switch dates are unaffected by Catalog edits.

## Migration

The existing db.create_all startup creates the Catalog table. An idempotent schema upgrade adds the nullable catalog_id foreign key in place and links missing relationships for active AND soft-deleted devices. Legacy rows link only when exactly one existing Catalog entry matches normalized Vendor/Model. Unmatched legacy values remain intact for manual assignment in Edit Switch. Existing Catalog links and user-edited Catalog names are retained on restart. No Switch table rebuild or old field removal is needed. Malformed legacy rows with blank vendor/model remain unlinked and retain their old display fallback.

All original device values—including IDs, asset/serial, production line, block, duplicate IP, status, notes, dates, soft-delete state and Passport UID—are preserved. Move History and PIN settings are unchanged. A pre-catalog SQLite backup is saved in backend/data.

## API

- GET /api/switch-catalog: list with active/non-deleted switch_count, calculated by one grouped outer-join query (zero-use models included).
- POST /api/switch-catalog: create name/vendor/model (required), description (optional).
- GET /api/switch-catalog/<id>: model details with calculated usage count.
- PATCH /api/switch-catalog/<id>: edit metadata; normalized duplicates return a readable validation error.
- POST /api/switches: the new web form submits catalog_id. Invalid/non-integer Catalog IDs are rejected; Vendor/Model supplied alongside catalog_id are ignored in favor of Catalog data.

New physical Switches require a valid integer catalog_id. POST /api/switches never creates Catalog records from free-text Vendor/Model. Vendor/Model fields submitted alongside a valid ID are not authoritative. Old snapshot columns remain for safe compatibility; reads resolve Catalog relationships dynamically.

Unused Catalog models support PIN-protected deletion as described below. Optional Catalog-owned image upload is implemented; see catalog-images.md.

## UI

Use the existing Switch Catalog sidebar item. The table contains exactly MODEL NAME, VENDOR, MODEL, SWITCHES, ACTIONS, with the shared search/sort/pagination foundation. Search matches name, vendor and model. Add and Edit share CatalogForm. View displays saved model metadata and active usage count.

The shared AddSwitch form used by Dashboard and Inventory loads Catalog choices on opening, sends the selected ID, and guides users to Catalog if empty. Existing controls and optional physical-device fields remain in place.

Production Line SW NAME now aggregates distinct Catalog friendly names from non-deleted devices, falling back to Vendor + Model for unlinked legacy devices. Production Line MODEL NAME, line status rules and Dashboard summary calculations are unchanged. Move retains catalog_id; soft delete decreases Catalog usage and Restore increases it. Catalog pages refresh after save; other pages load authoritative values on navigation. Existing Passport refresh behavior is unchanged.

## Validation

Backend: from backend, .venv/Scripts/python.exe -m unittest discover -s tests -q.
Frontend: from frontend, pnpm lint and pnpm build.
Browser checks use the isolated artifacts/catalog-browser-test.db, not live factory records. They cover catalog CRUD (Add/View/Edit only), normalized duplicates, empty/search states, shared Add Switch from both pages, edit propagation, Passport UID continuity, counts across Move/Delete/Restore and mobile sizing.

## Files changed

- backend/app/models.py
- backend/app/catalog_values.py (new)
- backend/app/schema.py
- backend/app/routes/catalog.py (new)
- backend/app/routes/switches.py
- backend/app/routes/production_lines.py
- backend/app/validation.py
- backend/app/__init__.py
- backend/tests/test_catalog.py (new)
- backend/tests/test_data.py
- frontend/src/App.jsx
- frontend/src/services/api.js
- frontend/src/pages/SwitchCatalog.jsx (new)
- frontend/src/components/forms/CatalogForm.jsx (new)
- frontend/src/components/forms/AddSwitch.jsx
- docs/switch-catalog.md (new)

## Catalog selection and protected deletion

Select beside Reset enables checkboxes without changing the five data columns. Header selection applies only to the current visible page. Search, Reset, sorting, pagination and page-size changes clear selection. Cancel exits selection mode.

POST /api/switch-catalog/delete-preview accepts {"ids": [1, 2]} and returns eligible/blocked lists, with names and reference counts. The confirmation lists both groups and requires the existing six-digit Delete PIN. Only the reviewed eligible IDs are submitted.

POST /api/switch-catalog/delete accepts {"ids": [1, 2], "pin": "<entered PIN>"}. It reuses the existing hashed PIN verification and failure lockout. A BEGIN IMMEDIATE transaction rechecks ALL physical Switch references, including Recycle Bin records, before deleting only unused Catalog rows. It returns deleted and blocked lists. No Switch data or relationships are modified; referenced Catalog rows cannot be removed. No schema migration is needed.

After success the list refreshes, selection clears, and pagination clamps safely. Used models can display zero active Switches but remain protected by archived references.

Validation: 62 backend tests pass, including PIN setup/format/change, wrong PIN, single/bulk/mixed delete, archived references, stale preview protection and unchanged Switch counts. Isolated browser checks cover selection, search/pagination, confirmation, PIN handling, Add/View/Edit, and mobile layout. Lint and production build pass.

## Add/Edit Switch Catalog integration

Inventory offers Edit alongside View, using the same AddSwitch form as Dashboard/Inventory creation. Catalog options use friendly name plus Vendor/Model; selection displays read-only supporting metadata. The existing native select is retained (native keyboard type-ahead, no custom full-text search). Loading, empty Catalog and retry states are explicit.

PATCH /api/switches/<id> edits existing physical-device fields and catalog_id under a serialized transaction. It rejects deleted records and location fields; Move Switch remains the relocation path. Catalog changes preserve ID, Passport UID, original dates, physical identifiers, location, status and Move History unless an allowed field is explicitly edited. updated_at uses the existing UTC storage/Bangkok serialization. There is no general Edit History system yet, so no new history system was added.

No new database columns or tables. All 13 existing live Switches were linked already; the database backup is backend/data/factory_network.pre-switch-edit-20260917.db. Backend regression fixtures now explicitly create/select Catalog records before creating physical Switches. 65 tests pass; frontend lint/build and isolated desktop/mobile Add/Edit browser tests pass.
