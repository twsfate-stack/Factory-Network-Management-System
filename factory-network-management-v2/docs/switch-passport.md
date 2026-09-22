# Switch Passport and QR labels

## Permanent identity and migration

Each Switch owns a random UUID4 passport_uid. The backend generates it on INSERT; Add Switch ignores client-supplied UIDs. Startup safely adds the column if missing and backfills only missing/empty values for both active and soft-deleted records. A unique index prevents reuse; SQLite triggers prevent changing a UID or inserting a missing UID. Existing Switch IDs, fields, dates, PIN settings and move history are preserved. Back up backend/data/factory_network.db before application updates.

Move, status change and restore keep the same UID. The Passport reads current values directly from Switch and snapshots directly from SwitchMoveHistory. No duplicate Passport/device/history table or QR image storage is introduced.

## Routes

- /passport/<passport_uid>: dedicated responsive React page, no sidebar.
- GET /api/passport/<passport_uid>: read-only selected Switch fields, last 10 moves newest-first, has_more_history, permanent UID and configured Passport URL. No PIN, hash or server secrets are returned. Invalid/unknown UIDs return a readable 404.
- GET /api/passport/<passport_uid>/qr.png: PNG generated locally with Segno 1.6.6 from the configured URL. Add ?download=1 for attachment download.

The Passport includes current location, identity, network, notes, saved creation/updated dates and move history. It refreshes on load, window focus/visibility and every 30 seconds while visible. Failed refreshes show an error and flag stale information. Archived devices retain their Passport with an explicit inventory warning. This page has no write, delete or move controls.

Existing move snapshots are reused. Status changes were not historically recorded and are not fabricated. The creation entry uses the stored created_at; older records whose timestamp was backfilled by an earlier milestone retain that fallback. Timestamps use the existing centralized UTC storage and Asia/Bangkok (+07:00) formatting.

## Stable factory URL

PUBLIC_BASE_URL is server configuration, never derived from Host headers or browser origin. It must be an HTTP(S) origin without credentials, path, query or fragment. Leave unset until the stable factory address is known; Passport data remains usable but QR generation/printing is unavailable. See backend/.env.example for the configuration name. The file is documentation; it is not automatically loaded.

PowerShell example, substituting the factory's real stable hostname:

```powershell
$env:PUBLIC_BASE_URL = 'http://fnms.company.local'
.venv/Scripts/python.exe run.py
```

For an explicitly temporary development test only, a loopback URL can be supplied via this environment variable. Do not print such labels for factory use. The isolated automated tests use a loopback test server and do not configure the live factory URL.

The normal production build can be served locally by Flask: build frontend first with pnpm build, then start the backend. Flask serves /, /passport/<uid>, and bundled /assets. Vite also supports direct Passport routes during development. PUBLIC_BASE_URL must point to the web frontend, not an /api URL.

Phone scanning requires network access to the configured FNMS host. No tunnel, Internet exposure, DNS registration or firewall change is provided. A stable DNS address must continue resolving after host-computer changes: changing PUBLIC_BASE_URL does not alter already printed QR codes. Preserve the original address to keep old labels reachable.

## Labels

Print QR Label invokes browser print. Print CSS includes only QMB FNMS, the QR, Asset ID, Serial Number and UID. No hostname, line or block appears on the permanent label. Turn off browser headers/footers and choose paper/scale appropriate to the label printer; the label is approximately 60 mm wide with a 42 mm QR and a four-module quiet zone. PNG download uses the immutable UID filename. No specialized printer integration is required.

## Validation

Run backend tests from backend with .venv/Scripts/python.exe -m unittest discover -s tests -q. Frontend: pnpm lint and pnpm build.

Tests cover legacy active/deleted migration and repeat startup, server UUID generation, uniqueness/immutability, API allowlist, QR payload, move/status/archive/restore, restart, history order/limit and stable QR bytes. Browser tests in ignored artifacts/passport-check.cjs use an isolated database and built Flask routes, including 320/390 px mobile layouts, printing, downloading and automatic data refresh. An independent QR decoder verifies the actual PNG payload. Physical printer and phone Wi-Fi connectivity require the site's final hostname and devices.

Segno documentation: https://segno.readthedocs.io/en/stable/serializers.html

## Files changed in this milestone

- backend/app/models.py
- backend/app/schema.py
- backend/app/__init__.py
- backend/app/routes/passport.py (new)
- backend/app/routes/frontend.py (new)
- backend/requirements.txt
- backend/requirements.lock.txt
- backend/.env.example (new)
- backend/tests/test_passport.py (new)
- backend/tests/test_security.py
- frontend/src/App.jsx
- frontend/src/services/api.js
- frontend/src/components/SwitchDetail.jsx
- frontend/src/pages/Dashboard.jsx
- frontend/src/pages/Passport.jsx (new)
- frontend/src/styles/passport.css (new)
- docs/switch-passport.md (new)
