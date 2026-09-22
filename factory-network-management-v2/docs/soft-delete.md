# Soft Delete and Delete PIN

## Usage

Open Settings > Delete Security > Set Delete PIN. Enter and confirm exactly six ASCII digits. The live database is intentionally left unconfigured; test PINs exist only in isolated test databases. Change PIN requires the current PIN. There is no default PIN and no web recovery bypass.

In Switch Inventory, click Select, choose one or more records, then Delete. The confirmation requires the PIN. Normal mode has no checkboxes or per-row Delete buttons. Selections remain attached to record IDs across sorting, filtering and pagination. Cancel clears selection. Open Recycle Bin from the table header to see deleted records; Restore returns a record after conflict validation.

## Storage and migration

switches.is_deleted is a non-null Boolean, default false. switches.deleted_at is a nullable DATETIME. Startup adds missing fields without recreating tables. security_settings is a singleton table constrained to id=1, containing delete_pin_hash, created_at, updated_at, failed_attempts and locked_until. Metadata counters support a shared persistent cooldown after five incorrect PIN guesses (one minute).

A consistent pre-soft-delete SQLite backup is in backend/data/factory_network.pre-soft-delete-20260911-223157.db. Applying the migration preserved every original field on all five existing Switches and both Production Lines. SQLite integrity_check returned ok. No live Switch was deleted and no live PIN was configured during testing. Database and backup files remain ignored by Git.

## PIN security

Werkzeug generate_password_hash uses its salted scrypt default; verification uses check_password_hash. The API never returns the hash or PIN. PIN inputs use password fields and are cleared on errors/success. No PIN is stored in localStorage, sessionStorage, environment configuration or frontend code. Tests generate temporary PINs at runtime. No new package was required.

SQLite BEGIN IMMEDIATE serializes setup/change/delete/restore transactions. Setup cannot overwrite an existing PIN, including concurrent setup attempts. Delete and Change PIN verify the hash on the backend. Wrong PINs cannot mutate Switch records; only security attempt metadata changes. Setup and PIN changes use server-generated timestamps. JSON POST requests are used; no PIN appears in URLs or request logs.

## API

- GET /api/settings/delete-pin/status returns only pin_configured.
- POST /api/settings/delete-pin/setup accepts new_pin and confirm_pin; fails if already configured.
- POST /api/settings/delete-pin/change accepts current_pin, new_pin and confirm_pin.
- POST /api/switches/delete accepts switch_ids and pin; returns success and deleted_count.
- POST /api/switches/restore accepts switch_ids; returns success and restored_count.
- GET /api/switches returns non-deleted records. Use deleted=true for Recycle Bin, including search/filter queries.
- GET /api/switches/:id retains access to the stored passport fields, including deletion metadata.

Delete/restore accept 1-500 distinct positive integer IDs. Unknown IDs or wrong record states reject the whole batch. Delete sets is_deleted=true and deleted_at to the server time. Restore sets false/null. Neither operation changes passport fields or the original created_at/updated_at; no permanent delete endpoint exists.

## Counts, conflicts and dates

Dashboard counts filter is_deleted=false. Production Line counts, status and unique vendor/model summaries use only non-deleted related Switches. No stored totals are updated. Inventory refreshes after delete/restore; Dashboard automatically loads updated summaries on navigation. An independently open tab does not receive push updates.

Existing global unique constraints on serial number and asset ID are retained. Deleted records reserve these values, so Add Switch cannot reuse them. Restore checks active records and the full restoring batch for hostname, serial and asset conflicts before changing anything. Hostname remains non-unique during normal creation as in the existing model, but conflicting hostnames prevent restore with a readable message. No data is silently merged or overwritten.

Deleted and settings timestamps reuse app/timezone.py: UTC DATETIME storage, Asia/Bangkok +07:00 ISO serialization, and YYYY-MM-DD HH:mm display in Bangkok time. No second timezone implementation is introduced.

## Files

Created:
- backend/app/routes/security.py
- backend/app/routes/recycle.py
- backend/tests/test_security.py
- frontend/src/components/forms/PinDialog.jsx
- frontend/src/pages/Settings.jsx
- docs/soft-delete.md

Modified:
- backend/app/models.py and app/schema.py
- backend/app/__init__.py
- backend/app/routes/switches.py, dashboard.py, production_lines.py
- backend/tests/test_data.py (expected table list)
- frontend/src/App.jsx and services/api.js
- frontend/src/pages/SwitchInventory.jsx
- frontend/src/components/ui/DataTable.jsx (accessible selection names)
- README.md

Dashboard JSX, Sidebar, theme tokens, CSS, Summary Cards, SearchInput and StatusBadge design were not changed. Earlier milestone changes remain intact.

## Validation

29 backend tests passed, covering setup, invalid formats/mismatch, existing PIN, wrong PIN, hash verification, single/bulk delete, atomic invalid-ID failures, cooldown, change PIN and old/new PIN behavior, recycle visibility, deleted-date offset, restore/conflict handling, unchanged passport fields, counts/line aggregation and repeatable legacy schema upgrades. Existing Add Switch and Production Line tests pass.

Frontend lint and production build passed. Browser tests against an isolated real SQLite backend covered existing Add Switch, first setup, deletion blocked before setup, wrong PIN, single delete, restore, PIN change, old PIN rejection, new PIN acceptance, bulk delete and Recycle Bin. Counts changed from 10 total/8 active to 9/7, back to 10/8 on restore, then 8/6 after bulk delete. No JavaScript errors or PIN browser storage were found.

## Limitations

There are no user accounts or role permissions: initial setup and restore are available to anyone who can access this internal application. PIN recovery remains a future server-admin procedure; no bypass is provided. Unique identifiers remain reserved while deleted. Restoring a conflicting hostname requires resolving the conflict in a future management feature. No permanent delete, history, move, QR, monitoring, import/export or other deferred features were added.

IP Address is optional and non-unique following the duplicate-IP revision. It never blocks restore. See duplicate-ip.md.
