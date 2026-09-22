import re
from uuid import uuid4
from .catalog_values import normalize_model_value


def upgrade_schema(engine):
    """Idempotent SQLite upgrades preserving rows and unrelated constraints."""
    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(switches)")}
            if "block" not in columns:
                connection.exec_driver_sql("ALTER TABLE switches ADD COLUMN block VARCHAR(100)")
            if "is_deleted" not in columns:
                connection.exec_driver_sql("ALTER TABLE switches ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0")
            if "deleted_at" not in columns:
                connection.exec_driver_sql("ALTER TABLE switches ADD COLUMN deleted_at DATETIME")
            for table in ("switches", "production_lines"):
                columns = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}
                for field in ("created_at", "updated_at"):
                    if field not in columns:
                        connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {field} DATETIME")
                # Unknown historical creation times use upgrade time; never replace known dates.
                connection.exec_driver_sql(f"UPDATE {table} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                connection.exec_driver_sql(f"UPDATE {table} SET updated_at = created_at WHERE updated_at IS NULL")
            migrate_line_models(connection)
            remove_ip_uniqueness(connection)
            migrate_passport_uids(connection)
            migrate_switch_catalog(connection)
            catalog_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(switch_catalog)")}
            if "image_filename" not in catalog_columns:
                connection.exec_driver_sql("ALTER TABLE switch_catalog ADD COLUMN image_filename VARCHAR(64)")
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'


def remove_ip_uniqueness(connection):
    indexes = connection.exec_driver_sql("PRAGMA index_list(switches)").all()
    ip_indexes = [row for row in indexes if row[2] and
                  [column[2] for column in connection.exec_driver_sql(f"PRAGMA index_info({quote_identifier(row[1])})")] == ["ip_address"]]
    if not ip_indexes:
        return
    for row in ip_indexes:
        if row[3] == "c":
            connection.exec_driver_sql(f"DROP INDEX {quote_identifier(row[1])}")
    if not any(row[3] == "u" for row in ip_indexes):
        return
    original = connection.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='switches'").scalar_one()
    # The old SQLAlchemy schema uses a table-level UNIQUE (ip_address).
    # Preserve its remaining SQL verbatim: collations, checks, foreign keys and extra columns.
    revised, count = re.subn(r',\s*UNIQUE\s*\(\s*ip_address\s*\)', '', original, flags=re.IGNORECASE)
    if count != 1:
        raise RuntimeError("Unrecognized IP constraint; database upgrade was rolled back.")
    objects = connection.exec_driver_sql("SELECT sql FROM sqlite_master WHERE tbl_name='switches' AND type IN ('index','trigger') AND sql IS NOT NULL").scalars().all()
    columns = ','.join(quote_identifier(row[1]) for row in connection.exec_driver_sql("PRAGMA table_info(switches)"))
    before_count = connection.exec_driver_sql("SELECT COUNT(*) FROM switches").scalar_one()
    connection.exec_driver_sql('CREATE TABLE switches_ip_upgrade (' + revised.split('(', 1)[1])
    connection.exec_driver_sql(f"INSERT INTO switches_ip_upgrade ({columns}) SELECT {columns} FROM switches")
    if connection.exec_driver_sql("SELECT COUNT(*) FROM switches_ip_upgrade").scalar_one() != before_count:
        raise RuntimeError("Switch copy verification failed; database upgrade was rolled back.")
    connection.exec_driver_sql("DROP TABLE switches")
    connection.exec_driver_sql("ALTER TABLE switches_ip_upgrade RENAME TO switches")
    for sql in objects:
        connection.exec_driver_sql(sql)
    if connection.exec_driver_sql("PRAGMA foreign_key_check").first():
        raise RuntimeError("Foreign key verification failed; database upgrade was rolled back.")


def migrate_line_models(connection):
    connection.exec_driver_sql("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    name = "production_line_model_names_v1"
    if connection.exec_driver_sql("SELECT 1 FROM schema_migrations WHERE name=?", (name,)).first():
        return
    columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(production_lines)")}
    for field in ("model", "model_name"):
        if field not in columns:
            continue
        for line_id, value in connection.exec_driver_sql(f'SELECT id, {field} FROM production_lines WHERE {field} IS NOT NULL').all():
            value = value.strip()
            if not value:
                continue
            existing = connection.exec_driver_sql("SELECT model_name FROM production_line_models WHERE production_line_id=?", (line_id,)).scalars().all()
            if value.casefold() not in {entry.casefold() for entry in existing}:
                connection.exec_driver_sql("INSERT INTO production_line_models (production_line_id,model_name,position,created_at) VALUES (?,?,?,CURRENT_TIMESTAMP)", (line_id, value, len(existing)))
    # Mark completion so a later user removal cannot be undone by startup re-import.
    connection.exec_driver_sql("INSERT INTO schema_migrations (name) VALUES (?)", (name,))


def migrate_passport_uids(connection):
    columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(switches)")}
    if "passport_uid" not in columns:
        connection.exec_driver_sql("ALTER TABLE switches ADD COLUMN passport_uid VARCHAR(36)")
    for switch_id, in connection.exec_driver_sql("SELECT id FROM switches WHERE passport_uid IS NULL OR trim(passport_uid) = ''").all():
        connection.exec_driver_sql("UPDATE switches SET passport_uid=? WHERE id=?", (str(uuid4()), switch_id))
    connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ux_switches_passport_uid ON switches(passport_uid)")
    # ALTER TABLE cannot add NOT NULL to existing rows; these also protect direct SQL writes.
    connection.exec_driver_sql("""CREATE TRIGGER IF NOT EXISTS passport_uid_required
        BEFORE INSERT ON switches WHEN NEW.passport_uid IS NULL OR length(trim(NEW.passport_uid)) != 36
        BEGIN SELECT RAISE(ABORT, 'Passport UID is required'); END""")
    connection.exec_driver_sql("""CREATE TRIGGER IF NOT EXISTS passport_uid_immutable
        BEFORE UPDATE OF passport_uid ON switches WHEN NEW.passport_uid IS NOT OLD.passport_uid
        BEGIN SELECT RAISE(ABORT, 'Passport UID cannot change'); END""")


def migrate_switch_catalog(connection):
    columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(switches)")}
    if "catalog_id" not in columns:
        connection.exec_driver_sql("ALTER TABLE switches ADD COLUMN catalog_id INTEGER REFERENCES switch_catalog(id)")
    connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_switches_catalog_id ON switches(catalog_id)")
    rows = connection.exec_driver_sql("SELECT id,vendor,model FROM switches WHERE catalog_id IS NULL ORDER BY id").all()
    for switch_id, vendor, model in rows:
        if not vendor or not model or not vendor.strip() or not model.strip():
            continue  # Preserve malformed legacy rows with their existing display fallback.
        keys = (normalize_model_value(vendor), normalize_model_value(model))
        matches = connection.exec_driver_sql("SELECT id FROM switch_catalog WHERE vendor_key=? AND model_key=?", keys).all()
        if len(matches) == 1:
            connection.exec_driver_sql("UPDATE switches SET catalog_id=? WHERE id=?", (matches[0][0], switch_id))
