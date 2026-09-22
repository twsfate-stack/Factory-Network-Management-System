# Production Line Model Names and six-column Overview

## Behavior

Both Dashboard and Production Lines use the same ProductionLineTable and GET /api/production-lines data. The six columns are Production Line, Model Name, SW Name, Total Switches, Status and Detail. Model Name joins line.model_names with a middle dot; an empty list displays an em dash. SW Name is the former SW Vendor column, still joining unique vendor/model combinations from non-deleted Switch records. For example Arista/7050, Arista/7060 and Quanta/LB9 display Arista 7050, Arista 7060 and Quanta LB9, independently of line Model Names.

Add Production Line has required Name, optional multiple Model Names and optional Description. Enter or + Add inserts a trimmed chip; its remove button deletes that chip before save. Duplicate names are rejected case-insensitively. Up to 50 names of 150 characters each are supported. Saving also includes any nonblank uncommitted draft so typed data is not silently lost.

The previous View modal remains at the same URL and still lists real Switch statuses. Its small Edit Production Line action opens the same AddProductionLine form in edit mode. No new detail page or navigation route was introduced. Save refreshes the current overview; Dashboard and Production Lines share the same saved list. Existing Switch status, line operational status, counters, PIN and soft-delete behavior are unchanged.

## Database and migration

production_line_models stores id, production_line_id (foreign key), model_name, position and created_at. A per-line unique constraint on model_name uses NOCASE; backend validation additionally checks Unicode casefold duplicates. position preserves user ordering. Retained names keep their row IDs/creation timestamps; removed names are deleted from this child table and newly added names become new rows. There is no comma-separated storage. Line updated_at changes on Model Name edits; timestamps use the existing UTC storage/Bangkok serialization convention.

The startup migration creates the relational table through SQLAlchemy and imports nonempty legacy model/model_name values as single trimmed names. Original columns and values remain untouched for safety. schema_migrations records completion once, so a name removed later by the user is not resurrected by re-import on restart. The migration uses the existing SQLite transaction and is repeatable.

A pre-model-names SQLite backup is in backend/data. Live migration verification preserved every original field on 5 Production Lines, 9 Switches and the security settings row. Both saved legacy Model values were imported once. integrity_check passed and foreign_key_check returned no errors.

## APIs

GET /api/production-lines returns model_names as an ordered array alongside existing switch_models, totals and operational status. POST accepts model_names (optional, default []). PATCH /api/production-lines/:id accepts name, description and/or model_names; omitted fields are preserved and [] clears all names. Validation and uniqueness failures roll back the transaction. Line IDs and Switch assignments remain stable. No duplicate detail API was added.

## Files

Created: frontend/src/components/forms/ModelNamesInput.jsx and docs/model-names.md.
Modified: backend/app/models.py, schema.py, routes/production_lines.py, tests/test_data.py; frontend/src/components/forms/AddProductionLine.jsx, components/ProductionLineTable.jsx, pages/Dashboard.jsx, pages/showcase/sampleData.js, services/api.js; README.md.

No changes to Sidebar, Switch Inventory, Add Switch, StatusBadge, inline status, delete/PIN/restore, or theme CSS were needed. Showcase model names are isolated sample data only.

## Validation

38 backend tests pass, including single/multiple names, trimming, duplicate/invalid input rejection, removal, case-only updates, edit atomicity, model/Switch name separation, counts/status, legacy import, preservation and no re-import after deletion. Existing Switch, duplicate-IP and security regression tests remain passing. Frontend lint and production build passed.

Browser tests against isolated SQLite verified three chips, Enter/+ Add, duplicate rejection, remove/edit, exactly six headers, identical saved names in both overviews, separate SW Name aggregation, totals/WORKING/NO SWITCH, empty em dashes, existing View modal, Switch Inventory navigation and reload persistence. Screenshots reviewed at 1366px. No live user data was used for acceptance edits.

Existing development-server/LAN deployment limitations remain; no new dependencies or unrelated features were added.
