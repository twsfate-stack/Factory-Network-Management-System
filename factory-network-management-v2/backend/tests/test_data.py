from switch_fixtures import post_switch
import tempfile
import sqlite3
from contextlib import closing
import unittest
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.models import db, ProductionLine, Switch


class DataTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "test.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.path.as_posix()}"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.directory.cleanup()

    def line(self, name="S27", description="bondi ag"):
        response = self.client.post("/api/production-lines", json={"name": name, "description": description})
        self.assertEqual(response.status_code, 201)
        return response.json["data"]["id"]

    def switch(self, line_id, **overrides):
        data = dict(hostname="SW-S27-001", vendor="Arista", model="7060", production_line_id=line_id, status="ACTIVE")
        data.update(overrides)
        return post_switch(self.client, json=data)

    def test_database_created_and_persistent(self):
        self.assertTrue(self.path.exists())
        with self.app.app_context():
            self.assertEqual(set(inspect(db.engine).get_table_names()), {"production_lines", "switches", "security_settings", "production_line_models", "schema_migrations", "switch_move_history", "switch_catalog"})
            self.assertEqual(db.session.execute(text("PRAGMA foreign_keys")).scalar(), 1)
        line_id = self.line()
        self.assertEqual(self.switch(line_id).status_code, 201)
        second = create_app(self.config)
        self.assertEqual(second.test_client().get("/api/dashboard").json["total_switches"], 1)
        with second.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_empty_summary_and_empty_line(self):
        self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=0, active=0, offline=0, spare=0))
        self.line()
        row = self.client.get("/api/production-lines").json[0]
        self.assertEqual(row["description"], "bondi ag")
        self.assertEqual(row["total_switches"], 0)
        self.assertEqual(row["status"], "NO SWITCH")
        self.assertEqual(row["switch_models"], [])

    def test_server_timestamps_acceptance_and_update(self):
        line_id = self.line("A10", "Bondi AG")
        before = datetime.now(timezone.utc)
        for number, vendor, model in ((1, "Arista", "7060"), (2, "Quanta", "LYB")):
            extra = dict(asset_id="AT001", ip_address="172.16.10.21", firmware_version="4.32.1F") if number == 1 else {}
            response = self.switch(line_id, hostname=f"SW-A10-00{number}", serial_number=f"SN00123{number + 3}", vendor=vendor, model=model, block=f"B0{number}", created_at="1999-01-01", updated_at="1999-01-01", **extra)
            self.assertEqual(response.status_code, 201)
            row = response.json["data"]
            created = datetime.fromisoformat(row["created_at"])
            self.assertGreaterEqual(created, before)
            self.assertLessEqual(created, datetime.now(timezone.utc))
            self.assertEqual(self.client.get(f"/api/switches/{row['id']}").json["created_at"], row["created_at"])
            self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=number, active=number, offline=0, spare=0))
            self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], number)
        with self.app.app_context():
            record = db.session.get(Switch, row["id"])
            created, updated = record.created_at, record.updated_at
            record.notes = "Updated through model"
            db.session.commit()
            self.assertEqual(record.created_at, created)
            self.assertGreater(record.updated_at, updated)

    def test_thailand_midnight_is_same_instant_as_database(self):
        from app.timezone import iso_thailand, THAILAND_TZ
        instant = datetime(2026, 9, 10, 17, 16, 32, tzinfo=timezone.utc)
        expected = "2026-09-11T00:16:32+07:00"
        self.assertEqual(iso_thailand(instant), expected)
        self.assertEqual(iso_thailand(instant.astimezone(THAILAND_TZ)), expected)
        line_id = self.line("A10")
        row = self.switch(line_id).json["data"]
        with self.app.app_context():
            record = db.session.get(Switch, row["id"])
            self.assertEqual(datetime.fromisoformat(row["created_at"]), record.created_at.replace(tzinfo=timezone.utc))
            record.created_at = instant.replace(tzinfo=None)
            record.updated_at = instant.replace(tzinfo=None)
            db.session.commit()
        detail = self.client.get(f"/api/switches/{row['id']}").json
        listing = self.client.get("/api/switches").json[0]
        for result in (detail, listing):
            self.assertEqual(result["created_at"], expected)
            self.assertEqual(result["updated_at"], expected)
            self.assertEqual(datetime.fromisoformat(result["created_at"]).astimezone(timezone.utc), instant)

    def test_timestamp_upgrade_preserves_rows_and_known_dates(self):
        line_id = self.line("A10")
        saved = self.switch(line_id, serial_number="LEGACY", block="B01").json["data"]
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("ALTER TABLE switches DROP COLUMN created_at")
            connection.execute("ALTER TABLE switches ADD COLUMN created_at DATETIME")
            connection.execute("ALTER TABLE production_lines DROP COLUMN created_at")
            connection.execute("ALTER TABLE production_lines DROP COLUMN updated_at")
            connection.commit()
        snapshots = []
        for _ in range(2):
            upgraded = create_app(self.config)
            client = upgraded.test_client()
            row = client.get(f"/api/switches/{saved['id']}").json
            self.assertEqual(row["updated_at"], saved["updated_at"])
            self.assertEqual((row["serial_number"], row["block"], row["production_line_id"]), ("LEGACY", "B01", line_id))
            self.assertIsNotNone(datetime.fromisoformat(row["created_at"]))
            snapshots.append((row, client.get("/api/production-lines").json))
            with upgraded.app_context():
                self.assertEqual(db.session.execute(text("PRAGMA integrity_check")).scalar(), "ok")
                db.session.remove()
                db.engine.dispose()
        self.assertEqual(snapshots[0], snapshots[1])

    def test_line_validation(self):
        for name in ("", "  ", [], 12):
            self.assertEqual(self.client.post("/api/production-lines", json={"name": name}).status_code, 400)
        self.line()
        response = self.client.post("/api/production-lines", json={"name": " s27 "})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["message"], "Production Line name already exists.")

    def test_create_switch_optional_fields_and_whitespace(self):
        response = self.switch(self.line(), hostname=" SW-S27-001 ", asset_id=" ", serial_number="")
        self.assertEqual(response.status_code, 201)
        row = response.json["data"]
        self.assertEqual(row["hostname"], "SW-S27-001")
        self.assertIsNone(row["asset_id"])
        self.assertIsNone(row["serial_number"])
        self.assertTrue(row["created_at"].endswith("+07:00"))
        self.assertEqual(len(self.client.get("/api/switches").json), 1)

    def test_counts_and_line_aggregation(self):
        first, second = self.line(), self.line("W17")
        for status in ("ACTIVE", "ACTIVE", "OFFLINE", "SPARE"):
            self.assertEqual(self.switch(first, status=status).status_code, 201)
        self.switch(first, vendor="LYB", model="LB9", status="ACTIVE")
        self.switch(second, status="SPARE")
        self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=6, active=3, offline=1, spare=2))
        rows = self.client.get("/api/production-lines").json
        self.assertEqual(rows[0]["total_switches"], 5)
        self.assertEqual(rows[0]["switch_models"], ["Arista 7060", "LYB LB9"])
        self.assertEqual(rows[0]["status"], "WORKING")
        self.assertEqual(rows[1]["status"], "NOT WORKING")

    def test_active_line_includes_spares(self):
        line_id = self.line()
        self.switch(line_id, status="SPARE")
        self.switch(line_id, status="ACTIVE")
        self.assertEqual(self.client.get("/api/production-lines").json[0]["status"], "WORKING")

    def test_inventory_block_serial_details_and_search(self):
        line_id = self.line("A10", "Bondi AG")
        response = self.switch(line_id, hostname="SW-A10-001", serial_number="SN001234", asset_id="AT001", ip_address="172.16.10.21", block=" B01 ", firmware_version="4.32.1F", notes="Rack notes")
        self.assertEqual(response.status_code, 201)
        row = response.json["data"]
        detail = self.client.get(f"/api/switches/{row['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json["block"], "B01")
        self.assertEqual(detail.json["serial_number"], "SN001234")
        self.assertEqual(detail.json["production_line"], "A10")
        self.assertEqual(detail.json["firmware"], "4.32.1F")
        self.assertEqual(detail.json["notes"], "Rack notes")
        for search in ("SW-A10-001", "sn001234", "AT001", "Arista", "7060", "172.16.10.21", "A10", "B01"):
            with self.subTest(search=search):
                self.assertEqual(len(self.client.get("/api/switches", query_string={"search": search}).json), 1)
        self.assertEqual(self.client.get("/api/switches/9999").json, {"success": False, "message": "Switch not found."})
        self.assertEqual(self.client.get("/api/switches/9999").status_code, 404)
        self.assertEqual(self.switch(line_id, block="x" * 101).status_code, 400)
        self.assertIsNone(self.switch(line_id, block=" ").json["data"]["block"])

    def test_block_upgrade_preserves_existing_rows_and_is_repeatable(self):
        line_id = self.line("A10", "Bondi AG")
        self.switch(line_id, serial_number="LEGACY-SERIAL", asset_id="LEGACY-ASSET")
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        # Create a pre-Block schema in this isolated test database.
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("ALTER TABLE switches DROP COLUMN block")
            before = connection.execute("SELECT * FROM switches").fetchall()
            line_before = connection.execute("SELECT * FROM production_lines").fetchall()
            original_columns = [row[1] for row in connection.execute("PRAGMA table_info(switches)")]
        for _ in range(2):
            upgraded = create_app(self.config)
            with upgraded.app_context():
                db.session.remove()
                db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute('SELECT ' + ','.join(original_columns) + ' FROM switches').fetchall(), before)
            self.assertEqual(connection.execute("SELECT * FROM production_lines").fetchall(), line_before)
            self.assertIsNone(connection.execute("SELECT block FROM switches").fetchone()[0])
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual([row[1] for row in connection.execute("PRAGMA table_info(switches)")].count("block"), 1)
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 1)
        self.assertEqual(self.switch(line_id, block="B02").json["data"]["block"], "B02")

    def test_exact_a10_workflow(self):
        line_id = self.line("A10", "Bondi AG")
        initial = self.client.get("/api/production-lines").json[0]
        self.assertEqual((initial["name"], initial["description"], initial["total_switches"]), ("A10", "Bondi AG", 0))
        for number, vendor, model in ((1, "Arista", "7060"), (2, "Quanta", "LYB")):
            response = self.switch(line_id, hostname=f"SW-A10-0{number}", vendor=vendor, model=model)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json["data"]["production_line_id"], line_id)
            self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=number, active=number, offline=0, spare=0))
            line = self.client.get("/api/production-lines").json[0]
            self.assertEqual(line["total_switches"], number)
            self.assertEqual(line["status"], "WORKING")
            self.assertEqual(line["switch_models"], ["Arista 7060"] if number == 1 else ["Arista 7060", "Quanta LYB"])
        self.assertEqual(len(self.client.get(f"/api/switches?production_line={line_id}").json), 2)

    def test_counters_are_derived_and_line_assignments_are_exclusive(self):
        response = self.client.post("/api/production-lines", json={"name": "A10", "description": "Bondi AG", "total_switches": 999, "active": 999})
        self.assertEqual(response.status_code, 201)
        first = response.json["data"]["id"]
        self.assertEqual(response.json["data"]["total_switches"], 0)
        second = self.line("S27")
        self.switch(first)
        self.switch(first)
        self.switch(second, vendor="Quanta", model="LB9", status="OFFLINE")
        lines = self.client.get("/api/production-lines").json
        self.assertEqual([(line["name"], line["total_switches"]) for line in lines], [("A10", 2), ("S27", 1)])
        self.assertEqual(lines[0]["switch_models"], ["Arista 7060"])
        with self.app.app_context():
            self.assertEqual({column["name"] for column in inspect(db.engine).get_columns("production_lines")}, {"id", "name", "description", "created_at", "updated_at"})
            foreign_keys = inspect(db.engine).get_foreign_keys("switches")
            self.assertTrue(any(key["constrained_columns"] == ["production_line_id"] and key["referred_table"] == "production_lines" for key in foreign_keys))

    def test_assigned_line_cannot_be_deleted_or_orphaned(self):
        line_id = self.line("A10")
        self.switch(line_id)
        with self.app.app_context():
            with self.assertRaises(IntegrityError):
                db.session.execute(db.delete(ProductionLine).where(ProductionLine.id == line_id))
                db.session.commit()
            db.session.rollback()
            switch = db.session.scalars(db.select(Switch)).one()
            switch.production_line_id = None
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            switch.production_line_id = line_id + 999
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            db.session.delete(db.session.get(ProductionLine, line_id))
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            self.assertEqual(db.session.get(Switch, switch.id).production_line_id, line_id)
        self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], 1)

    def test_duplicate_asset(self):
        self.check_duplicate("asset_id", "AT001", "at001", "Asset ID")

    def test_duplicate_serial(self):
        self.check_duplicate("serial_number", "ABC123", "abc123", "Serial number")

    def test_duplicate_ip(self):
        line = self.line("A10")
        for hostname in ("SW-A10-01", "SW-A10-02"):
            self.assertEqual(self.switch(line, hostname=hostname, ip_address="172.19.0.8").status_code, 201)
        records = self.client.get("/api/switches").json
        self.assertEqual([row["ip_address"] for row in records], ["172.19.0.8", "172.19.0.8"])
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 2)
        self.assertEqual(self.client.get("/api/production-lines").json[0]["total_switches"], 2)
        for address in ("2001:db8::1", "2001:0db8:0:0:0:0:0:1"):
            self.assertEqual(self.switch(line, ip_address=address).status_code, 201)
        with self.app.app_context():
            row = db.session.scalars(db.select(Switch).where(Switch.ip_address == "2001:db8::1")).first()
            row.ip_address = "172.19.0.8"
            db.session.commit()

    def check_duplicate(self, key, first, second, label):
        line_id = self.line()
        self.assertEqual(self.switch(line_id, **{key: first}).status_code, 201)
        response = self.switch(line_id, **{key: second})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, dict(success=False, message=f"{label} already exists."))
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 1)
        self.assertEqual(self.switch(line_id).status_code, 201)

    def test_invalid_switch_fields(self):
        line_id = self.line()
        for fields in ({"hostname": " "}, {"model": ""}, {"vendor": ""}, {"status": "UNKNOWN"}, {"status": []}, {"production_line_id": 999}, {"production_line_id": True}, {"production_line_id": "1"}, {"ip_address": "bad-ip"}, {"hostname": 5}, {"notes": "x" * 4001}):
            with self.subTest(fields=fields):
                response = self.switch(line_id, **fields)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json["success"])
        self.assertEqual(self.client.get("/api/dashboard").json["total_switches"], 0)

    def test_json_validation_and_filters(self):
        self.assertEqual(post_switch(self.client, json=[]).status_code, 400)
        self.assertEqual(self.client.post("/api/switches", data="{").status_code, 400)
        first, second = self.line(), self.line("W17")
        self.switch(first, asset_id="ASSET-001")
        self.switch(second, vendor="LYB", model="LB9", status="OFFLINE", hostname="SW-W17")
        for query in (f"production_line={first}", "status=OFFLINE", "vendor=LYB", "search=asset-001", "search=LB9", "search=SW-W17", f"production_line={second}&status=OFFLINE&vendor=LYB&search=LB9"):
            self.assertEqual(len(self.client.get(f"/api/switches?{query}").json), 1)
        self.assertEqual(self.client.get("/api/switches?search=%25").json, [])
        self.assertEqual(self.client.get("/api/switches?status=BAD").status_code, 400)

    def test_inline_status_transitions_and_dates(self):
        line = self.line("A10")
        row = self.switch(line, hostname="s8g").json["data"]
        endpoint = f"/api/switches/{row['id']}/status"
        created = row["created_at"]
        for status in ("SPARE", "ACTIVE", "OFFLINE", "ACTIVE", "SPARE", "OFFLINE", "ACTIVE"):
            previous = row["updated_at"]
            before = datetime.now(timezone.utc)
            response = self.client.patch(endpoint, json={"status": status, "hostname": "not applied", "created_at": "not applied"})
            self.assertEqual(response.status_code, 200)
            row = response.json["data"]
            self.assertEqual(row["status"], status)
            self.assertEqual(row["hostname"], "s8g")
            self.assertEqual(row["created_at"], created)
            self.assertNotEqual(row["updated_at"], previous)
            self.assertTrue(row["updated_at"].endswith("+07:00"))
            self.assertGreaterEqual(datetime.fromisoformat(row["updated_at"]), before)
            expected = dict(total_switches=1, active=0, offline=0, spare=0)
            expected[status.lower()] = 1
            self.assertEqual(self.client.get("/api/dashboard").json, expected)
            line_data = self.client.get("/api/production-lines").json[0]
            self.assertEqual((line_data["total_switches"], line_data["status"]), (1, "WORKING" if status == "ACTIVE" else "NOT WORKING"))
            self.assertEqual(self.client.patch(endpoint, json={"status": status}).json["data"], row)
        second = create_app(self.config)
        self.assertEqual(second.test_client().get(f"/api/switches/{row['id']}").json, row)
        with second.app_context():
            db.session.remove(); db.engine.dispose()

    def test_inline_status_invalid_deleted_and_failed_commit(self):
        from unittest.mock import patch
        from sqlalchemy.exc import SQLAlchemyError
        row = self.switch(self.line()).json["data"]
        endpoint = f"/api/switches/{row['id']}/status"
        for status in (None, "active", "REPAIR", [], 1, "ACTIVE "):
            self.assertEqual(self.client.patch(endpoint, json={"status": status}).status_code, 400)
        self.assertEqual(self.client.patch('/api/switches/99999/status', json={"status": "SPARE"}).status_code, 404)
        with patch.object(db.session, "commit", side_effect=SQLAlchemyError("simulated failure")):
            with self.assertLogs(self.app.logger, level="ERROR"):
                response = self.client.patch(endpoint, json={"status": "SPARE"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("simulated failure", response.get_data(as_text=True))
        self.assertEqual(self.client.get(f"/api/switches/{row['id']}").json, row)
        with self.app.app_context():
            record = db.session.get(Switch, row["id"])
            record.is_deleted = True
            db.session.commit()
        before = self.client.get(f"/api/switches/{row['id']}").json
        self.assertEqual(self.client.patch(endpoint, json={"status": "SPARE"}).status_code, 400)
        self.assertEqual(self.client.get(f"/api/switches/{row['id']}").json, before)

    def test_production_line_operational_status_cases(self):
        cases = [(["ACTIVE", "OFFLINE"], "WORKING"), (["ACTIVE", "SPARE"], "WORKING"),
                 (["OFFLINE"], "NOT WORKING"), (["OFFLINE", "SPARE"], "NOT WORKING"),
                 (["SPARE", "SPARE"], "NOT WORKING"), ([], "NO SWITCH"),
                 (["ACTIVE"] * 3 + ["OFFLINE"] * 2 + ["SPARE"], "WORKING"),
                 (["OFFLINE"] * 5 + ["SPARE"], "NOT WORKING")]
        for number, (statuses, expected) in enumerate(cases):
            line_id = self.line(f"CASE-{number}")
            for status in statuses:
                self.switch(line_id, status=status)
            line = next(row for row in self.client.get("/api/production-lines").json if row["id"] == line_id)
            self.assertEqual((line["total_switches"], line["status"]), (len(statuses), expected))
            details = self.client.get(f"/api/switches?production_line={line_id}").json
            self.assertEqual([row["status"] for row in details], statuses)

    def test_deleted_active_does_not_make_line_working(self):
        line_id = self.line("A10")
        first = self.switch(line_id, status="ACTIVE").json["data"]
        self.switch(line_id, status="OFFLINE")
        with self.app.app_context():
            db.session.get(Switch, first["id"]).is_deleted = True
            db.session.commit()
        line = self.client.get("/api/production-lines").json[0]
        self.assertEqual((line["total_switches"], line["status"]), (1, "NOT WORKING"))
        self.assertEqual(self.client.get("/api/dashboard").json, dict(total_switches=1, active=0, offline=1, spare=0))

    def test_line_multiple_model_names_create_edit_and_separation(self):
        response = self.client.post('/api/production-lines', json={"name": "A10", "model_names": [" S8Z PDB ", "S8Z", "Bondi AG"], "description": "Bondi production line"})
        self.assertEqual(response.status_code, 201)
        line = response.json["data"]
        self.assertEqual(line["model_names"], ["S8Z PDB", "S8Z", "Bondi AG"])
        self.assertEqual((line["switch_models"], line["total_switches"], line["status"]), ([], 0, "NO SWITCH"))
        for model in ("7050", "7060", "7060"):
            self.switch(line["id"], model=model)
        current = self.client.get('/api/production-lines').json[0]
        self.assertEqual(current["switch_models"], ["Arista 7050", "Arista 7060"])
        self.assertEqual(current["model_names"], line["model_names"])
        self.assertEqual((current["total_switches"], current["status"]), (3, "WORKING"))
        created = line["created_at"]
        updated = self.client.patch(f"/api/production-lines/{line['id']}", json={"model_names": ["S8Z PDB", "Bondi AG", "Bondi AG Gen2"]})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["data"]["model_names"], ["S8Z PDB", "Bondi AG", "Bondi AG Gen2"])
        self.assertEqual(updated.json["data"]["created_at"], created)
        self.assertGreater(datetime.fromisoformat(updated.json["data"]["updated_at"]), datetime.fromisoformat(line["updated_at"]))
        self.assertEqual(self.client.patch(f"/api/production-lines/{line['id']}", json={"model_names": []}).json["data"]["model_names"], [])
        with self.app.app_context():
            self.assertEqual(db.session.execute(text('SELECT COUNT(*) FROM production_line_models')).scalar(), 0)

    def test_model_names_validation_and_atomic_edits(self):
        line_id = self.line('A10')
        for names in (["S8Z", " s8z "], [" "], [12], "comma,separated", None, ["x" * 151], [str(i) for i in range(51)]):
            with self.subTest(names_type=type(names).__name__):
                self.assertEqual(self.client.post('/api/production-lines', json={"name": "NEW", "model_names": names}).status_code, 400)
                self.assertEqual(self.client.patch(f'/api/production-lines/{line_id}', json={"name": "CHANGED", "model_names": names}).status_code, 400)
        self.assertEqual(self.client.get('/api/production-lines').json[0]["name"], "A10")
        self.assertEqual(self.client.post('/api/production-lines', json={"name": "W17", "model_names": ["S8Z"]}).status_code, 201)
        self.assertEqual(self.client.patch(f'/api/production-lines/{line_id}', json={"name": "w17", "model_names": ["S8Z"]}).status_code, 400)
        self.assertEqual(self.client.get('/api/production-lines').json[0]["model_names"], [])
        self.assertEqual(self.client.patch('/api/production-lines/99999', json={"model_names": []}).status_code, 404)
        self.assertEqual(self.client.patch(f'/api/production-lines/{line_id}', json={"model_names": ["S8Z"]}).status_code, 200)
        self.assertEqual(self.client.patch(f'/api/production-lines/{line_id}', json={"model_names": ["s8z"]}).status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.execute(text('SELECT COUNT(*) FROM production_line_models WHERE production_line_id=:id'), {"id": line_id}).scalar(), 1)

    def test_model_names_legacy_migration_once_preserves_originals(self):
        line_id = self.line('LEGACY')
        self.switch(line_id)
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as c:
            c.execute('ALTER TABLE production_lines ADD COLUMN model VARCHAR(150)')
            c.execute('UPDATE production_lines SET model=?', (' Bondi AG ',))
            c.execute("DELETE FROM schema_migrations WHERE name='production_line_model_names_v1'")
            c.commit()
            before = {table:c.execute(f'SELECT * FROM {table}').fetchall() for table in ('production_lines','switches','security_settings')}
        def restart():
            app = create_app(self.config)
            with app.app_context():
                db.session.remove(); db.engine.dispose()
        restart(); restart()
        self.assertEqual(self.client.get('/api/production-lines').json[0]['model_names'], ['Bondi AG'])
        with closing(sqlite3.connect(self.path)) as c:
            for table,rows in before.items():
                self.assertEqual(c.execute(f'SELECT * FROM {table}').fetchall(), rows)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM production_line_models').fetchone()[0],1)
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.client.patch(f'/api/production-lines/{line_id}', json={"model_names": []})
        restart()
        self.assertEqual(self.client.get('/api/production-lines').json[0]['model_names'], [])
