# Inline Switch status change

Inventory now wraps the existing StatusBadge in a borderless semantic button. Its location, size and colors are unchanged. The new InlineSwitchStatus component uses the existing dropdown-menu styles and StatusBadge options, with a checkmark and aria-checked for the current status. The menu is portaled outside the scrolling table, positioned near the badge, and closes on selection, outside click, Escape, blur, scroll or resize. Arrow keys, Home/End and Enter are supported. Busy requests disable the trigger. No PIN is requested.

PATCH /api/switches/:id/status accepts only status ACTIVE, OFFLINE or SPARE and returns success plus the saved record. No suitable update API previously existed. SQLite serializes the write with soft-delete operations; deleted records are rejected. The same status causes no row update. Normal updates use the existing SQLAlchemy updated_at default, preserve created_at and return Asia/Bangkok +07:00 timestamps. No schema migration or new package was needed.

The UI replaces the row only after a successful API response, so failures retain the previous status and show a concise inline error. Existing table filtering/sorting follows the saved row. Dashboard and Production Line summaries continue deriving from database status, excluding deleted records; opening those views automatically fetches the new calculations without a browser reload. This follows the current page data flow; independent browser tabs do not receive push updates.

Created: frontend/src/components/InlineSwitchStatus.jsx and this document.
Modified: backend/app/routes/switches.py, backend/tests/test_data.py, frontend/src/services/api.js, frontend/src/pages/SwitchInventory.jsx.
Unchanged: StatusBadge source and colors, Dashboard JSX, table columns and layout, Add Switch, selection/delete/PIN, Recycle Bin, Settings, Sidebar and shared design system. Recycle Bin badges remain read-only.

Validation: all 33 backend tests pass, including ACTIVE/SPARE/OFFLINE transitions, exact status validation, missing/deleted records, same-status no-op, persistence, derived summaries, unchanged creation date, Bangkok update time, and failed-commit rollback. Frontend lint and final production build pass. Browser tests with s8g in an isolated database verified transitions, persistence/reload, total staying 1 while status counts change, line status recalculation, checked choice, outside click, Escape/arrows/Enter, no request for same status, disabled loading and simulated API failure retaining the old badge. No test changed the user's live records.
