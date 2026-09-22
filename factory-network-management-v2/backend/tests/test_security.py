from switch_fixtures import post_switch
import secrets
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone, timedelta
from werkzeug.security import check_password_hash
from app import create_app
from app.models import db, SecuritySettings, Switch


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "security.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.path.as_posix()}"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.pin = f"{secrets.randbelow(1000000):06d}"
        self.other = f"{(int(self.pin) + 1) % 1000000:06d}"
        self.line = self.client.post("/api/production-lines", json={"name": "A10", "description": "Bondi AG"}).json["data"]["id"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp.cleanup()

    def setup_pin(self):
        return self.client.post("/api/settings/delete-pin/setup", json={"new_pin": self.pin, "confirm_pin": self.pin})

    def add(self, name="SW-A10-001", status="ACTIVE", **extra):
        response = post_switch(self.client, json=dict(hostname=name, production_line_id=self.line, vendor="Arista", model="7060", block="B01", status=status, **extra))
        self.assertEqual(response.status_code, 201)
        return response.json["data"]

    def delete(self, ids, pin=None):
        return self.client.post("/api/switches/delete", json={"switch_ids": ids, "pin": self.pin if pin is None else pin})

    def test_setup_hash_status_and_no_overwrite(self):
        self.assertEqual(self.client.get("/api/settings/delete-pin/status").json, {"pin_configured": False})
        self.assertEqual(self.setup_pin().status_code, 201)
        self.assertEqual(self.setup_pin().status_code, 400)
        self.assertEqual(self.client.get("/api/settings/delete-pin/status").json, {"pin_configured": True})
        with self.app.app_context():
            record = db.session.get(SecuritySettings, 1)
            self.assertNotEqual(record.delete_pin_hash, self.pin)
            self.assertTrue(record.delete_pin_hash.startswith("scrypt:"))
            self.assertTrue(check_password_hash(record.delete_pin_hash, self.pin))
            self.assertIsNotNone(record.created_at)
        for endpoint in ("/api/settings/delete-pin/status", "/api/switches", "/api/dashboard", "/api/production-lines"):
            self.assertNotIn("delete_pin_hash", self.client.get(endpoint).get_data(as_text=True))

    def test_formats_and_mismatch(self):
        for pin in (None, 123456, "12345", "1234567", "abcdef", "１２３４５６", "123 56"):
            response = self.client.post("/api/settings/delete-pin/setup", json={"new_pin": pin, "confirm_pin": pin})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post("/api/settings/delete-pin/setup", json={"new_pin": self.pin, "confirm_pin": self.other}).status_code, 400)
        self.assertFalse(self.client.get("/api/settings/delete-pin/status").json["pin_configured"])

    def test_unconfigured_and_wrong_pin_do_not_delete(self):
        row = self.add()
        self.assertIn("not configured", self.delete([row["id"]]).json["message"])
        self.setup_pin()
        self.assertEqual(self.delete([row["id"]], self.other).json["message"], "Incorrect PIN.")
        self.assertEqual(self.client.get(f"/api/switches/{row['id']}").json, row)

    def test_single_bulk_delete_restore_and_counts(self):
        self.setup_pin()
        records = [self.add(f"SW-{i}", status, serial_number=f"SN-{i}") for i, status in enumerate(("ACTIVE", "OFFLINE", "SPARE"))]
        first = records[0]
        before = datetime.now(timezone.utc)
        self.assertEqual(self.delete([first["id"]]).json, {"success": True, "deleted_count": 1})
        self.assertEqual(self.client.get("/api/switches?search=SW-0").json, [])
        deleted = self.client.get("/api/switches?deleted=true").json[0]
        self.assertTrue(deleted["is_deleted"])
        self.assertTrue(deleted["deleted_at"].endswith("+07:00"))
        self.assertGreaterEqual(datetime.fromisoformat(deleted["deleted_at"]), before)
        for key, value in first.items():
            if key not in ("is_deleted", "deleted_at"):
                self.assertEqual(deleted[key], value)
        self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=2, active=0, offline=1, spare=1))
        self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], 2)
        self.assertEqual(self.delete([r["id"] for r in records[1:]]).json["deleted_count"], 2)
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 0)
        line = self.client.get("/api/production-lines").json[0]
        self.assertEqual(line["switch_models"], [])
        self.assertEqual(line["status"], "NO SWITCH")
        restored = self.client.post("/api/switches/restore", json={"switch_ids": [r["id"] for r in records]})
        self.assertEqual(restored.json["restored_count"], 3)
        self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=3, active=1, offline=1, spare=1))
        self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], 3)
        self.assertEqual(self.client.get("/api/switches?deleted=true").json, [])
        self.assertEqual(self.client.get(f"/api/switches/{first['id']}").json, first)

    def test_ids_validation_and_atomicity(self):
        self.setup_pin()
        row = self.add()
        for ids in ([], [True], ["1"], [row["id"], row["id"]], [row["id"], 9999], None):
            self.assertEqual(self.delete(ids).status_code, 400)
            self.assertEqual(self.client.post("/api/switches/restore", json={"switch_ids": ids}).status_code, 400)
        self.assertFalse(self.client.get(f"/api/switches/{row['id']}").json["is_deleted"])
        self.assertEqual(self.delete([row["id"]]).status_code, 200)
        self.assertEqual(self.delete([row["id"]]).status_code, 400)

    def test_restore_conflict_rolls_back_batch_and_reserves_identifiers(self):
        self.setup_pin()
        first, second = self.add("same", asset_id="RESERVED"), self.add("other")
        self.delete([first["id"], second["id"]])
        self.add("same")
        response = self.client.post("/api/switches/restore", json={"switch_ids": [first["id"], second["id"]]})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Hostname same is already in use", response.json["message"])
        self.assertEqual(len(self.client.get("/api/switches?deleted=true").json), 2)
        response = post_switch(self.client, json=dict(hostname="new", vendor="Arista", model="7060", status="ACTIVE", production_line_id=self.line, asset_id="RESERVED"))
        self.assertEqual(response.status_code, 400)

    def test_change_pin_and_throttling(self):
        self.setup_pin()
        row = self.add()
        endpoint = "/api/settings/delete-pin/change"
        data = dict(current_pin=self.other, new_pin=self.other, confirm_pin=self.other)
        self.assertEqual(self.client.post(endpoint, json=data).json["message"], "Incorrect current PIN.")
        data["current_pin"] = self.pin
        self.assertEqual(self.client.post(endpoint, json=data).status_code, 200)
        self.assertEqual(self.delete([row["id"]]).json["message"], "Incorrect PIN.")
        self.assertEqual(self.delete([row["id"]], self.other).status_code, 200)
        self.client.post("/api/switches/restore", json={"switch_ids": [row["id"]]})
        for _ in range(5):
            self.delete([row["id"]])
        self.assertIn("one minute", self.delete([row["id"]], self.other).json["message"])
        with self.app.app_context():
            db.session.get(SecuritySettings, 1).locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
            db.session.commit()
        self.assertEqual(self.delete([row["id"]], self.other).status_code, 200)

    def test_upgrade_preserves_original_data(self):
        row = self.add(serial_number="LEGACY")
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            c.execute("ALTER TABLE switches DROP COLUMN is_deleted")
            c.execute("ALTER TABLE switches DROP COLUMN deleted_at")
            c.execute("DROP TABLE security_settings")
            c.commit()
            columns = [r[1] for r in c.execute("PRAGMA table_info(switches)")]
            before = c.execute("SELECT * FROM switches").fetchall()
        for _ in range(2):
            upgraded = create_app(self.config)
            with upgraded.app_context():
                db.session.remove(); db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute("SELECT " + ",".join(columns) + " FROM switches").fetchall(), before)
            self.assertEqual(c.execute("SELECT is_deleted, deleted_at FROM switches").fetchone(), (0, None))
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(self.client.get(f"/api/switches/{row['id']}").json, row)

    def test_restore_allows_duplicate_ip(self):
        self.setup_pin()
        first = self.add("SW-A10-01", ip_address="172.19.0.8")
        self.delete([first["id"]])
        self.add("SW-A10-02", ip_address="172.19.0.8")
        response = self.client.post("/api/switches/restore", json={"switch_ids": [first["id"]]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 2)
        self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], 2)

    def test_legacy_unique_ip_migration_preserves_all_data(self):
        self.setup_pin()
        first = self.add("SW-A10-01", ip_address="172.19.0.8", serial_number="SN-IP", asset_id="ASSET-IP")
        self.delete([first["id"]])
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            sql = c.execute("SELECT sql FROM sqlite_master WHERE name='switches'").fetchone()[0]
            indexes = [r[0] for r in c.execute("SELECT sql FROM sqlite_master WHERE tbl_name='switches' AND type='index' AND sql IS NOT NULL")]
            c.execute("CREATE TABLE legacy_switches (" + sql.split('(',1)[1].rsplit(')',1)[0] + ", UNIQUE (ip_address))")
            c.execute("INSERT INTO legacy_switches SELECT * FROM switches")
            c.execute("DROP TABLE switches")
            c.execute("ALTER TABLE legacy_switches RENAME TO switches")
            for index in indexes:
                c.execute(index)
            c.execute("CREATE INDEX switches_block_custom ON switches(block)")
            c.execute("CREATE TRIGGER switches_custom AFTER UPDATE ON switches BEGIN SELECT 1; END")
            c.commit()
            columns = [r[1] for r in c.execute("PRAGMA table_info(switches)")]
            snapshots = {t: c.execute(f"SELECT * FROM {t} ORDER BY id").fetchall() for t in ('switches','production_lines','security_settings')}
            objects = c.execute("SELECT name,sql FROM sqlite_master WHERE tbl_name='switches' AND type IN ('index','trigger') AND sql IS NOT NULL ORDER BY name").fetchall()
        for _ in range(2):
            upgraded = create_app(self.config)
            with upgraded.app_context():
                db.session.remove(); db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            for table, rows in snapshots.items():
                self.assertEqual(c.execute(f"SELECT * FROM {table} ORDER BY id").fetchall(), rows)
            self.assertEqual([r[1] for r in c.execute("PRAGMA table_info(switches)")], columns)
            self.assertEqual(c.execute("SELECT name,sql FROM sqlite_master WHERE tbl_name='switches' AND type IN ('index','trigger') AND sql IS NOT NULL AND name NOT IN ('passport_uid_required','passport_uid_immutable') ORDER BY name").fetchall(), objects)
            self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            unique_columns = [[r[2] for r in c.execute(f'PRAGMA index_info("{idx[1]}")')] for idx in c.execute("PRAGMA index_list(switches)").fetchall() if idx[2]]
            self.assertNotIn(["ip_address"], unique_columns)
            self.assertIn(["asset_id"], unique_columns)
            self.assertIn(["serial_number"], unique_columns)
        self.add("SW-A10-02", ip_address="172.19.0.8")
        self.assertEqual(self.client.post("/api/switches/restore", json={"switch_ids": [first["id"]]}).status_code, 200)
