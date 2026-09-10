# Factory Network Management System

**V2 — Clean Rebuild · Sprint 0 — Foundation**

A new, independent foundation for an internal factory network management application.
This sprint establishes the design system and technical structure for visual review.
It contains no operational factory features and does not use any previous project's code or database.

## Structure

```text
factory-network-management-v2/
  frontend/
    src/
      assets/fonts/          Optional manually supplied display font
      components/layout/    App shell, sidebar and page structure
      components/ui/        Reusable controls and surfaces
      config/               Navigation definitions
      pages/showcase/       Development-only examples and isolated mock rows
      pages/Placeholder.jsx Planned section placeholder
      styles/theme.css      Semantic tokens, Tailwind and component styles
      App.jsx
      main.jsx
    package.json
    pnpm-lock.yaml
    pnpm-workspace.yaml
    vite.config.js
    eslint.config.js
    index.html
  backend/
    app/routes/health.py
    app/__init__.py
    tests/test_health.py
    run.py
    requirements.txt
    requirements.lock.txt
  docs/
    architecture.md
    validation.md
    files-created.md
  scripts/README.md
  README.md
  .gitignore
```

## Prerequisites

- Node.js 22.13+ (or Node 24 LTS), and pnpm 11.19.0.
- Python 3.11+; validated with Python 3.12.
- A modern Edge, Chrome, Firefox or Safari browser.
- Internet for the initial dependency install, or a prepared local package cache. Normal application use has no CDN dependency.

If pnpm is not installed, use `npm install --global pnpm@11.19.0` once.
Frontend packages are locked in pnpm-lock.yaml; backend packages are locked in requirements.lock.txt.

## Start development (Windows PowerShell)

Open two terminals in this new V2 project folder.

Terminal 1 — frontend:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Terminal 2 — backend:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe run.py
```

On subsequent starts, run only `pnpm dev` and `.\.venv\Scripts\python.exe run.py` from their respective folders.
No PowerShell activation policy changes are needed.
On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows Python command.

Open **http://127.0.0.1:5173/#/showcase** for the UI Showcase. Development opens the Showcase by default.
The Showcase is not a sidebar item. All six sidebar links navigate to intentional Sprint 0 placeholders.
The production build excludes the Showcase and its JavaScript sample data; production starts at Dashboard's placeholder.

Health endpoint: **http://127.0.0.1:5050/api/health**

```json
{"status":"ok","application":"Factory Network Management System"}
```

The frontend's Vite proxy also forwards `/api/health` to Flask, without a CORS dependency.
The frontend itself does not require Flask to display the foundation preview.
Both development servers bind to loopback only. Flask's development-server notice is expected; LAN deployment is a later sprint.

## Validation commands

```powershell
# frontend/
pnpm lint
pnpm build
pnpm preview

# backend/
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Invoke-RestMethod http://127.0.0.1:5050/api/health
```

Production preview defaults to http://127.0.0.1:4173 and deliberately does not expose the development Showcase.
The `/api` proxy is development-only; production serving and LAN access remain future work.

## Theme and typography

`frontend/src/styles/theme.css` owns the semantic palette, spacing, corner radii, typography, shadows and motion duration.
Tailwind v4 is integrated with its Vite plugin and `@import "tailwindcss"`; `@theme inline` maps semantic colors to utility classes such as `bg-background` and `text-foreground`.
Components use semantic variables rather than scattered color values. The four required palette values are also printed as descriptive labels in the Showcase.

- Background `#F7F7F7`; secondary surface `#EEEEEE`; primary text/action `#393E46`; muted decoration `#929AAB`.
- Supporting text uses darker `--text-secondary` for readable contrast. The muted palette color is used for decoration, not essential small text.
- Danger/error red is a separate semantic action token, not a switch status palette.
- Active, Offline and Spare badges have neutral dot/outline/square variants. Status colors are deferred.
- Controls share 40px minimum height and 10px radius. Cards use 16px; search and badges use pill radii.
- A 4px spacing rhythm and 160ms interaction transitions keep the interface consistent. Reduced motion is respected.
- Body/control typography uses local system fonts, with Leelawadee UI and Tahoma for Thai when installed. No fonts are fetched from a CDN.

### Add SF Distant Galaxy later

1. Obtain a font file you have permission to use.
2. Place it at `frontend/src/assets/fonts/SF Distant Galaxy.ttf` with that exact filename.
3. Restart Vite or rebuild.

`main.jsx` discovers the optional file with Vite's glob import and registers it using the browser FontFace API.
The display token `--font-brand` then uses it for major titles only. Missing or invalid files safely fall back to local Arial/system sans-serif without a missing-asset request.
Tables, fields, buttons, labels and descriptions always retain the UI font.

## Sprint boundary

Included: React/Vite, Tailwind, Flask application factory and health route, responsive shell, six planned navigation sections, semantic theme, UI components, isolated Showcase samples, and development documentation.

Not included: any database, SQLite, SQLAlchemy, migrations, real Dashboard, switch/catalog/line CRUD, search/filter logic, import/export, history storage, movement, authentication/PIN, QR, monitoring, ping, SNMP, deployment infrastructure or LAN configuration.

Only local, disposable UI state exists. Refresh clears it. The future system should use one host-owned backend/database for all LAN clients, not separate browser databases.

## Portability

Copy source and lockfiles. Omit `node_modules`, `.venv`, `dist`, caches, logs and temporary artifacts when zipping the folder; `.gitignore` excludes these from Git but does not automatically exclude them from a manually created ZIP.
Reinstall dependencies on the new machine. No absolute machine paths are embedded in the application.
The existing workspace Git repository is reused; no nested repository or automatic commit is created.
Suggested reviewed milestone/tag: `sprint-0-foundation`.

**Stop here: review and approve the Sprint 0 visual language before Sprint 1.**
