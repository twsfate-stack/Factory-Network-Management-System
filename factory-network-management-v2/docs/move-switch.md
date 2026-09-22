# Move Switch

Open Dashboard or Production Lines, choose a line's View action, then MOVE beside a non-deleted switch. Choose a stored destination line, enter its block (optional) and hostname (required), and optionally enter a note. Continue opens a read-only FROM/TO review; Back preserves inputs. Only Confirm Move saves.

## API and validation

- POST /api/switches/<id>/move: production_line_id (integer), hostname (1–150 trimmed characters), block (optional, up to 100), notes (optional, up to 4000). The UI also sends expected_updated_at to reject a stale review.
- GET /api/switches/<id>/moves: persistent move history, oldest first, including after soft delete.

Moves retain switch ID, asset ID, serial number, vendor/model, status, IP, notes and created_at. Existing hostname rules allow duplicates. Duplicate IP remains valid. The destination must exist; deleted switches and unchanged destinations are rejected. Moving within the same line is valid when block or hostname changes. No Delete PIN is required.

## Persistence and schema

The existing startup db.create_all() safely creates only the new switch_move_history table and its switch ID index. Existing tables/records are not replaced. Each entry stores switch ID, source/destination line IDs and name snapshots, blocks, hostnames, moved_at, and optional move note. Snapshots keep names readable after line renaming. No full activity UI is introduced; history is available through the read-only API.

BEGIN IMMEDIATE serializes writes with the existing status/delete logic. The backend loads old values, validates, changes the existing switch and inserts history in one transaction. An error rolls back both. All server times use the existing centralized UTC storage / Asia-Bangkok ISO 8601 (+07:00) serializer. Switch updated_at equals moved_at; created_at is unchanged.

After success, the current line View and Dashboard aggregates are fetched again. Source/destination totals, SW Names and operational statuses remain calculated from non-deleted records. Inventory and Switch View load updated database values on navigation. There is no cross-browser push synchronization in this milestone.

## Validation

Backend: .venv/Scripts/python.exe -m unittest discover -s tests -q (from backend).
Frontend: pnpm lint and pnpm build (from frontend).
The browser acceptance test in ignored artifacts/move-check.cjs uses an isolated database on port 5051; no live records are moved by tests.
