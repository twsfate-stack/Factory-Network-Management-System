import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from sqlalchemy import event
from app import create_app
from app.models import db, Switch, SwitchCatalog


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "catalog.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + self.path.as_posix()}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.line = self.client.post("/api/production-lines", json={"name": "H17", "model_names": ["Bondi AG"]}).json["data"]["id"]
        self.entry = self.client.post("/api/switch-catalog", json={"name": "Arista 7050", "vendor": "Arista", "model": "7050SX3-48YC8", "description": "Production network switch"}).json["data"]
        self.url = f"/api/switch-catalog/{self.entry['id']}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.directory.cleanup()

    def add(self, **extra):
        return self.client.post("/api/switches", json=dict(hostname="S8ZE", production_line_id=self.line, catalog_id=self.entry["id"], status="ACTIVE") | extra)

    def test_create_view_edit_and_normalized_duplicates(self):
        self.assertEqual(self.entry["switch_count"], 0)
        self.assertEqual(self.client.get(self.url).json["model"], "7050SX3-48YC8")
        for vendor, model in [(" arista ", "7050sx3-48yc8"), ("ARISTA", "7050SX3-48YC8")]:
            response = self.client.post("/api/switch-catalog", json={"name": "Another name", "vendor": vendor, "model": model})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json["message"], "This switch model already exists in the catalog.")
        other = self.client.post("/api/switch-catalog", json={"name": "LB9", "vendor": "Quanta", "model": "LB9"}).json["data"]
        self.assertEqual(self.client.patch(f"/api/switch-catalog/{other['id']}", json={"vendor": "arista", "model": "7050sx3-48yc8"}).status_code, 400)
        self.assertEqual(self.client.patch(self.url, json={"name": " Arista 7050SX3 "}).json["data"]["name"], "Arista 7050SX3")
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertEqual(self.client.get("/api/switch-catalog/9999").status_code, 404)
        for key in ["name", "vendor", "model"]:
            self.assertEqual(self.client.patch(self.url, json={key: " "}).status_code, 400)
        self.assertEqual(self.add(catalog_id=9999).status_code, 400)
        self.assertEqual(self.add(catalog_id=True).status_code, 400)

    def test_shared_source_updates_all_displays_without_rewriting_devices(self):
        first = self.add(asset_id="AT-7050-01", serial_number="77777", ip_address="172.19.0.8").json["data"]
        second = self.add(hostname="S8A", asset_id="AT-7050-02", ip_address="172.19.0.8").json["data"]
        self.assertEqual(first["catalog_id"], second["catalog_id"])
        self.assertEqual(len(self.client.get("/api/switch-catalog").json), 1)
        self.assertEqual(self.client.get(self.url).json["switch_count"], 2)
        with closing(sqlite3.connect(self.path)) as c:
            before = c.execute("SELECT * FROM switches ORDER BY id").fetchall()
        self.client.patch(self.url, json={"name": "Arista 7050SX3", "vendor": "Arista Networks", "model": "7050 Gen2"})
        after = self.client.get(f"/api/switches/{first['id']}").json
        self.assertEqual((after["vendor"], after["model"], after["catalog_name"]), ("Arista Networks", "7050 Gen2", "Arista 7050SX3"))
        passport = self.client.get("/api/passport/" + first["passport_uid"]).json
        self.assertEqual(passport["switch"]["model"], "7050 Gen2")
        self.assertEqual(passport["passport_uid"], first["passport_uid"])
        line = self.client.get("/api/production-lines").json[0]
        self.assertEqual(line["switch_models"], ["Arista 7050SX3"])
        self.assertEqual(line["model_names"], ["Bondi AG"])
        for filters in ({"search": "Gen2"}, {"vendor": "Arista Networks"}, {"search": "7050SX3"}):
            self.assertEqual(len(self.client.get("/api/switches", query_string=filters).json), 2)
        with closing(sqlite3.connect(self.path)) as c:
            self.assertEqual(c.execute("SELECT * FROM switches ORDER BY id").fetchall(), before)

    def test_move_status_delete_restore_counts(self):
        record = self.add(serial_number="77777").json["data"]
        target = self.client.post("/api/production-lines", json={"name": "A10"}).json["data"]["id"]
        self.assertEqual(self.client.post(f"/api/switches/{record['id']}/move", json={"production_line_id": target, "hostname": "S8A", "block": "A10-01"}).status_code, 200)
        after = self.client.get(f"/api/switches/{record['id']}").json
        self.assertEqual((after["catalog_id"], after["passport_uid"]), (record["catalog_id"], record["passport_uid"]))
        self.assertEqual(self.client.get(self.url).json["switch_count"], 1)
        self.client.patch(f"/api/switches/{record['id']}/status", json={"status": "SPARE"})
        self.assertEqual(self.client.get(self.url).json["switch_count"], 1)
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})
        self.assertEqual(self.client.post("/api/switches/delete", json={"switch_ids": [record["id"]], "pin": "123456"}).status_code, 200)
        self.assertEqual(self.client.get(self.url).json["switch_count"], 0)
        self.assertEqual(self.client.post("/api/switches/restore", json={"switch_ids": [record["id"]]}).status_code, 200)
        self.assertEqual(self.client.get(self.url).json["switch_count"], 1)
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 1)
        self.assertEqual(len(self.client.get(f"/api/switches/{record['id']}/moves").json), 1)

    def test_legacy_migration_preserves_rows_and_deduplicates(self):
        self.client.post("/api/switch-catalog", json={"name": "7060", "vendor": "Arista", "model": "7060"})
        self.client.post("/api/switch-catalog", json={"name": "LB9", "vendor": "Quanta", "model": "LB9"})
        with self.app.app_context():
            for number, vendor, model in [(1, "Arista", "7060"), (2, " arista ", "7060 "), (3, "Quanta", "LB9")]:
                db.session.add(Switch(hostname=f"legacy-{number}", vendor=vendor, model=model, production_line_id=self.line, status="ACTIVE", is_deleted=number == 2))
            db.session.commit()
            db.session.remove()
            db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            sql = c.execute("SELECT sql FROM sqlite_master WHERE name='switches'").fetchone()[0]
            sql, n = re.subn(r'\s*catalog_id INTEGER,', '', sql)
            self.assertEqual(n, 1)
            sql, n = re.subn(r',\s*FOREIGN KEY\(catalog_id\) REFERENCES switch_catalog \(id\)', '', sql)
            self.assertEqual(n, 1)
            columns = [r[1] for r in c.execute("PRAGMA table_info(switches)") if r[1] != "catalog_id"]
            columns_sql = ','.join(columns)
            before = c.execute(f"SELECT {columns_sql} FROM switches ORDER BY id").fetchall()
            c.execute(sql.replace("CREATE TABLE switches", "CREATE TABLE legacy_switches", 1))
            c.execute(f"INSERT INTO legacy_switches ({columns_sql}) SELECT {columns_sql} FROM switches")
            c.execute("DROP TABLE switches")
            c.execute("ALTER TABLE legacy_switches RENAME TO switches")
            c.commit()
        ids = None
        for _ in range(2):
            app = create_app(self.config)
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
            with closing(sqlite3.connect(self.path)) as c:
                self.assertEqual(c.execute(f"SELECT {columns_sql} FROM switches ORDER BY id").fetchall(), before)
                current = c.execute("SELECT catalog_id FROM switches ORDER BY id").fetchall()
                self.assertEqual(current[0], current[1])
                self.assertNotEqual(current[0], current[2])
                if ids: self.assertEqual(current, ids)
                ids = current
                self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(c.execute("SELECT COUNT(*) FROM switch_catalog").fetchone()[0], 3)

    def test_new_switch_requires_catalog_without_creating_one(self):
        before = self.client.get("/api/switch-catalog").json
        response = self.client.post("/api/switches", json=dict(hostname="new", vendor="Other", model="Other", production_line_id=self.line, status="ACTIVE"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.get("/api/switch-catalog").json, before)

    def test_edit_catalog_preserves_identity_location_status_and_counts(self):
        first = self.add(serial_number="77777", asset_id="AT-01", block="H17-03", ip_address="172.19.0.8").json["data"]
        other = self.client.post("/api/switch-catalog", json=dict(name="LB9", vendor="Quanta", model="LB9")).json["data"]
        url = f"/api/switches/{first['id']}"
        result = self.client.patch(url, json={"catalog_id": other["id"], "vendor": "Fake", "model": "Fake", "passport_uid": "fake", "created_at": "fake"})
        self.assertEqual(result.status_code, 200)
        changed = result.json["data"]
        for key in ("id", "serial_number", "asset_id", "hostname", "production_line_id", "block", "status", "passport_uid", "created_at"):
            self.assertEqual(first[key], changed[key], key)
        self.assertEqual(changed["model"], "LB9")
        self.assertNotEqual(changed["updated_at"], first["updated_at"])
        self.assertTrue(changed["updated_at"].endswith("+07:00"))
        self.assertEqual(self.client.get(self.url).json["switch_count"], 0)
        self.assertEqual(self.client.get(f"/api/switch-catalog/{other['id']}").json["switch_count"], 1)
        self.assertEqual(self.client.get("/api/production-lines").json[0]["switch_models"], ["LB9"])
        self.assertEqual(self.client.get("/api/passport/"+first["passport_uid"]).json["switch"]["model"], "LB9")
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 1)
        for payload in ({"catalog_id": 99999}, {"catalog_id": None}, {"catalog_id": True}, {"status": "invalid"}, {"ip_address": "bad"}, {"production_line_id": self.line}, {"block": "new"}):
            self.assertEqual(self.client.patch(url, json=payload).status_code, 400)
            self.assertEqual(self.client.get(url).json, changed)
        self.add(asset_id="AT-02", serial_number="other", ip_address="172.19.0.8")
        self.assertEqual(self.client.patch(url, json={"ip_address": "172.19.0.8"}).status_code, 200)
        for payload in ({"asset_id": "AT-02"}, {"serial_number": "other"}):
            self.assertEqual(self.client.patch(url, json=payload).status_code, 400)
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})
        self.client.post("/api/switches/delete", json={"switch_ids": [first["id"]], "pin": "123456"})
        self.assertEqual(self.client.patch(url, json={"catalog_id": self.entry["id"]}).status_code, 400)
        self.client.post("/api/switches/restore", json={"switch_ids": [first["id"]]})
        self.assertEqual(self.client.get(url).json["catalog_id"], other["id"])

    def test_unmatched_legacy_preserved_then_manually_assigned(self):
        with self.app.app_context():
            row = Switch(hostname="legacy", vendor="Unmatched", model="Old", production_line_id=self.line, status="SPARE")
            db.session.add(row)
            db.session.commit()
            record_id = row.id
            db.session.remove()
            db.engine.dispose()
        app = create_app(self.config)
        with app.app_context():
            record = db.session.get(Switch, record_id)
            self.assertIsNone(record.catalog_id)
            self.assertEqual((record.vendor, record.model), ("Unmatched", "Old"))
            db.session.remove()
            db.engine.dispose()
        url = f"/api/switches/{record_id}"
        self.assertEqual(self.client.get(url).json["vendor"], "Unmatched")
        response = self.client.patch(url, json={"catalog_id": self.entry["id"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["vendor"], "Arista")

    def test_list_counts_use_one_aggregate_query(self):
        for number in range(10):
            self.client.post("/api/switch-catalog", json={"name": str(number), "vendor": "Test", "model": str(number)})
        statements = []
        def track(connection, cursor, statement, parameters, context, many):
            if statement.lstrip().upper().startswith("SELECT"): statements.append(statement)
        with self.app.app_context():
            event.listen(db.engine, "before_cursor_execute", track)
            try:
                self.assertEqual(len(self.client.get("/api/switch-catalog").json), 11)
            finally:
                event.remove(db.engine, "before_cursor_execute", track)
        self.assertEqual(len(statements), 1)
