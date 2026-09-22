# Switch Inventory CSV import / export

## Scope and UI

Switch Inventory has Import and Export alongside its existing actions. Recycle Bin has neither action. Add/Edit/Move/Status/PIN/Passport behavior is unchanged. This milestone supports CSV only; there was no existing Excel dependency, and no new dependency was added. For Excel, use Save As > CSV UTF-8 (comma delimited). The modal gives a headers-only template, file selection, validation summary and paginated row-level preview before Confirm Import. Errors disable confirmation. Successful import closes the flow and refreshes Inventory; Dashboard, Catalog counts and Line summaries continue deriving data on their existing refresh/navigation paths.

## API

- GET /api/switches/import/template: headers-only UTF-8 BOM CSV.
- POST /api/switches/import/preview: multipart file; returns total/valid/errors, every row's result/reasons and a SHA-256 fingerprint. Does not insert data.
- POST /api/switches/import/confirm: uploads the original file again plus its preview fingerprint; independently parses, resolves master data and validates again under BEGIN IMMEDIATE, then inserts all rows in one transaction.
- GET /api/switches/export?scope=all: current non-deleted records.
- GET /api/switches/export?scope=current&search=...&production_line=...&status=...&vendor=...: same search fields and exact filter values as Inventory, including all matching pages. Production Line is the human-readable name for this endpoint. Existing GET /switches filter conventions are unchanged.

Empty exports return a readable JSON error; no empty download is silently created. Exports use fresh backend data, not the browser's cached rows. Changes committed by other users since the table loaded may therefore appear in the export.

## Template and matching

hostname,serial_number,asset_id,switch_model,ip_address,production_line,block,firmware,mac_address,status,notes

Required columns/values: hostname, switch_model, production_line, status. Other fields may be blank or omitted and use existing null conventions. Header case and spaces are normalized explicitly (Serial Number becomes serial_number). Duplicate/unknown headers and internal fields are rejected, including IDs, dates, Passport UID, deletion flags and image fields.

Catalog friendly names and Production Line names match by trimmed, case-insensitive exact text. Unknown or ambiguous matches are errors. Import never creates master data. Linked Catalog Vendor/Model and images remain authoritative. Hostname/text lengths, IP syntax, Catalog/Line existence and Switch creation values use the same backend validator as Add Switch. Status is trimmed and uppercased to ACTIVE/OFFLINE/SPARE. No new MAC or hostname format restrictions.

Serial Number and Asset ID remain globally unique under SQLite NOCASE, including soft-deleted records. Duplicate values are caught both within the file (all affected rows identified) and against the database. IP duplicates and hostname duplicates remain allowed, matching current Add Switch rules.

## Transaction and upload safety

Maximum input 5 MiB, 5,000 rows; multipart envelope 6 MiB. Only one CSV upload is accepted. UTF-8 decoding, CSV parser, expected headers and row widths are checked. Invalid encoding, binary NUL, malformed quotes, missing/duplicate headers, empty files and header-only files receive readable errors. CSV data is never executed. Imports are not saved in Catalog media or a permanent directory; request-scoped temporary streams are closed by Flask/Werkzeug.

Confirm re-uploads the file rather than trusting browser preview JSON. The fingerprint detects file changes; it is not an authorization token. The backend always revalidates current data under a write transaction. Any validation/insertion error rolls back the whole import. Browser controls prevent duplicate clicks, and failed confirmation requires preview again. No automatic retry is performed. If a connection is interrupted during confirmation, check Inventory before retrying: the existing application has no durable import-job/idempotency registry.

Switch timestamps and Passport UUIDs use the existing model defaults and centralized Bangkok serialization. No schema, migration, system settings or PIN changes.

## Export and round trip

Columns: hostname,serial_number,asset_id,switch_model,vendor,model,ip_address,production_line,block,firmware,mac_address,status,notes,created_at,updated_at.

Catalog names/Vendor/Model resolve dynamically, with existing legacy fallback. Production Line is exported as a name. Dates are ISO 8601 with +07:00; filenames use Asia/Bangkok time. CSV uses the standard writer, UTF-8 BOM and correct quoting for Thai, commas, quotes and newlines. Dangerous spreadsheet formula-leading values are prefixed with an apostrophe in the download only. Database values remain unchanged.

Exports are reports, not directly reimportable system-field dumps. To use an export as the basis for a new import, copy the template's eleven columns and omit vendor/model/generated dates. Formula-neutralizing apostrophes are deliberately retained as literals if reimported; review those uncommon values rather than stripping protection automatically. New imports get new system timestamps and Passport IDs. Matching master data must already exist.

## Validation

Existing 71 backend regression tests plus 7 new transfer tests cover a 100-row import, all-or-nothing rollback with forced insertion failure, missing/ambiguous references, DB/file duplicates including Recycle Bin, duplicate IP, invalid files, stale preview, system-field rejection, 120 active/10 archived export, 43-result filtered export, round-trip basis, Thai and formula safety.

Isolated browser checks cover template download, invalid preview, 100-row confirmation/refresh, export across pagination, Recycle Bin exclusion, empty export, mobile and JavaScript errors. Frontend lint/build pass. All test records stay in isolated databases; live production data is untouched.

## Source changes

Created backend/app/switch_creation.py, backend/app/routes/inventory_transfer.py, backend/tests/test_inventory_transfer.py, frontend/src/components/forms/InventoryTransfer.jsx and this document.

Modified backend/app/routes/switches.py (shared create validation), backend/app/__init__.py (routes/upload limit), frontend/src/services/api.js, frontend/src/components/ui/DataTable.jsx (optional criteria callback), frontend/src/pages/SwitchInventory.jsx and frontend/src/styles/theme.css (preview width only).

## Excel inventory and movement report

Export Format now offers Excel (.xlsx), selected by default, and the existing CSV option. `GET /api/switches/export?format=xlsx` returns a real openpyxl workbook with exactly `Switch Inventory` and `Move History`. Omitting format still returns CSV for compatibility. Import remains CSV-only and unchanged.

Both scopes exclude Recycle Bin switches. Current Results applies existing search/filters to physical switches, then exports every `switch_move_history` row linked to those switch IDs, including moves from earlier lines. Historical hostname/location values come from saved move snapshots; Serial Number, Asset ID and Switch Model come from the current linked switch. No additional history table or schema changes.

Both sheets have bold headers, frozen first rows, filters and readable widths. Empty history still gets its header-only sheet. Excel dates are native date cells displayed as `yyyy-mm-dd hh:mm:ss` in Asia/Bangkok; conversion happens once before removing timezone information for Excel. Text remains literal text, including formula-looking strings and Thai. CSV retains its original headers, timestamp format and formula protection.

Validation: 80 backend tests passed, including all moves for filtered switches, deleted-record exclusion, empty history, Thai text, literal formulas, firmware preservation and UTC-to-Bangkok conversion across midnight. Frontend lint/build and Excel/CSV browser downloads passed. A read-only snapshot of current data yielded 2 Inventory rows and 1 genuine Move History row; the workbook was read back and checked against SQLite. Live records were not modified.
