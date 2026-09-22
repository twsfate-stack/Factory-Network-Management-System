# Allow duplicate IP addresses

Removed Switch.ip_address unique=True and the existing SQLite table-level UNIQUE (ip_address) constraint. The field remains nullable VARCHAR(45). IP format parsing/normalization is unchanged. Removed the IP-specific duplicate error mapping and IP from restore conflict checks. Hostname, serial number and asset ID rules are unchanged. No edit endpoint exists; model-level updates now accept duplicate IPs too.

The startup upgrade detects the old constraint. SQLite cannot drop this table constraint directly, so a transactional table rebuild copies every column, preserves the remaining CREATE TABLE definitions, and recreates explicit indexes/triggers. Row counts and foreign keys are checked before commit. Repeated startup is a no-op once the constraint is absent. Explicit single-column unique IP indexes, if present, are removed too. No database reset or record deletion occurs.

A consistent pre-duplicate-IP backup was created in backend/data before migration. Live upgrade verification compared every original field in switches, production_lines and security_settings: all six switches, three lines and one settings row were preserved. Integrity check passed and foreign-key check returned no errors. Asset and serial unique constraints remain present.

Changed code: backend/app/models.py, schema.py, validation.py and routes/recycle.py. Updated tests: backend/tests/test_data.py and test_security.py. Documentation: this file, data-foundation.md and soft-delete.md. No frontend or PIN/soft-delete behavior was redesigned.

Validation: 31 backend tests passed, including same-IP creation/counting, IPv6 normalization with duplicates, model update, restore with another active switch using the same IP, and legacy-constraint migration preserving rows, timestamps, PIN hash, other uniqueness constraints, indexes and triggers. The frontend production build passed. A browser test saved two switches through the existing form using 172.19.0.8; both appeared in Inventory and counted separately in Dashboard and Production Line summaries. Browser tests used an isolated database.
