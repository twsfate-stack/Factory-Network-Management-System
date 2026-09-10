# Persistent data

Flask creates `factory_network.db` here on first startup. It starts empty; no demo records are seeded.
This directory is independent of frontend builds and excluded from Git except this note.
Keep the database when updating application source. Stop Flask before copying the database for a backup.
Set FACTORY_DATABASE_PATH to an absolute alternative path if needed. Never put real data in dist or a test directory.
