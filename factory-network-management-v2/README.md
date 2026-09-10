# Factory Network Management System V2

**Sprint 1 — Data foundation**

A lightweight factory network application using React, Vite, Tailwind CSS, Flask, Flask-SQLAlchemy and SQLite. The approved Sprint 0 design is preserved. Dashboard counts, Production Lines and Add Switch now use real persistent data.

## Start on Windows

Prerequisites: Node.js 22.13+ (Node 24 LTS recommended), pnpm 11.19.0, and Python 3.11+ (tested with 3.12). Install pnpm once with `npm install --global pnpm@11.19.0` if needed.

From this V2 folder, open two PowerShell terminals.

Backend:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe run.py
```

Frontend:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

For later starts, only run the final command in each terminal. No virtual-environment activation is required. On macOS/Linux use python3 and .venv/bin/python instead of the Windows Python paths.

Open **http://127.0.0.1:5173/#/dashboard**. API health is **http://127.0.0.1:5050/api/health**. Port 5050 avoids the earlier service on port 5000.

## First real entry

1. Open Dashboard: all counts start at zero.
2. Click **Add Production Line**, enter `S27` and optional description `bondi ag`, then save.
3. Click **Add Switch** and enter `SW-S27-001`, Vendor `Arista`, Model `7060`, Production Line `S27`, Status `ACTIVE`.
4. Leave Serial Number blank if unavailable. Optional Asset ID, IP, MAC, Firmware and Notes are inside **More details**.
5. Save: Dashboard total and active counts become 1; S27 shows Arista 7060, quantity 1 and ACTIVE immediately.
6. Click **View** to see the switches assigned to that line.

The Production Lines menu provides the same live table and add actions. Other business sections remain placeholders. No database editor or server restart is needed to add records.

## Storage and safety of updates

The database is **backend/data/factory_network.db**, automatically created empty on first startup. It is outside frontend build output and ignored by Git. No demo records are automatically seeded. Preserve it across application updates. Stop Flask before copying the database for backup. Set FACTORY_DATABASE_PATH to an absolute file path to use another storage location.

Dependencies, .venv, node_modules, dist, logs and artifacts are excluded from source control. A manual ZIP must also exclude generated content; .gitignore does not filter a ZIP automatically. Move the database separately if you want to transfer real data.

## Structure

```text
frontend/src/
  components/layout/     Approved application shell
  components/ui/         Reusable approved UI primitives and DataTable
  components/forms/      Add Production Line / Add Switch forms
  components/ProductionLineTable.jsx
  services/api.js        Central API client
  pages/Dashboard.jsx    Live data and refresh lifecycle
  pages/showcase/        Development-only isolated mock preview
  styles/theme.css       Existing theme and design tokens
backend/
  app/models.py          ProductionLine and Switch SQLAlchemy models
  app/validation.py      Readable form/constraint errors
  app/routes/            Health, dashboard, lines, switches
  data/                  Persistent SQLite location
  tests/                 Isolated database/HTTP tests
  run.py
  requirements.txt
  requirements.lock.txt
docs/
  data-foundation.md     Current schema, endpoints, rules, validation and limitations
  architecture.md       Historical Sprint 0 architecture
  validation.md         Historical Sprint 0 validation
scripts/
```

## Validation

```powershell
# backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# frontend
pnpm lint
pnpm build
```

Tests use temporary databases, never the real database. Browser acceptance used a separate ignored test database. Full details and the modified-file list are in [docs/data-foundation.md](docs/data-foundation.md).

## Existing design system

Review the development-only Showcase at **http://127.0.0.1:5173/#/showcase**. It retains isolated mock rows and is excluded from production JavaScript. The live Dashboard opens by default.

Theme tokens remain in frontend/src/styles/theme.css. Add a legally obtained `SF Distant Galaxy.ttf` under frontend/src/assets/fonts/ and restart Vite/rebuild to use the optional display font. Missing fonts safely fall back; UI text retains the system sans-serif font. No runtime CDN fonts are used.

frontend/.env.example uses VITE_API_BASE_URL=/api; the Vite proxy forwards to Flask. Production hosting should provide a same-origin /api route. Standalone Vite preview does not proxy the backend; deployment/LAN hosting is out of scope.

## Milestone boundary

Implemented: SQLite tables, create/list Production Lines and Switches, real Dashboard summaries, five-column line summaries, basic View, validation, and refresh after saving.

Not implemented: authentication, roles, QR, edit/delete, PIN, history storage, import/export, SNMP/ping, topology, service/repair management, Docker or production deployment. No automatic continuation beyond this milestone.

Git checkpoints: `sprint-0-ui-approved` preserves the approved foundation; `sprint-1-data-foundation` marks the completed integration. The existing workspace Git repository is used.