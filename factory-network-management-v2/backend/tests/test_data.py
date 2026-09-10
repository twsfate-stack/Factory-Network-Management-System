import tempfile
import unittest
from pathlib import Path
from sqlalchemy import inspect, text
from app import create_app
from app.models import db


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
        return self.client.post("/api/switches", json=data)

    def test_database_created_and_persistent(self):
        self.assertTrue(self.path.exists())
        with self.app.app_context():
            self.assertEqual(set(inspect(db.engine).get_table_names()), {"production_lines", "switches"})
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
        self.assertIsNone(row["status"])
        self.assertEqual(row["switch_models"], [])

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
        self.assertTrue(row["created_at"].endswith("Z"))
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
        self.assertEqual(rows[0]["status"], "OFFLINE")
        self.assertEqual(rows[1]["status"], "SPARE")

    def test_active_line_includes_spares(self):
        line_id = self.line()
        self.switch(line_id, status="SPARE")
        self.switch(line_id, status="ACTIVE")
        self.assertEqual(self.client.get("/api/production-lines").json[0]["status"], "ACTIVE")

    def test_duplicate_asset(self):
        self.check_duplicate("asset_id", "AT001", "at001", "Asset ID")

    def test_duplicate_serial(self):
        self.check_duplicate("serial_number", "ABC123", "abc123", "Serial number")

    def test_duplicate_ip(self):
        self.check_duplicate("ip_address", "2001:db8::1", "2001:0db8:0:0:0:0:0:1", "IP address")

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
        self.assertEqual(self.client.post("/api/switches", json=[]).status_code, 400)
        self.assertEqual(self.client.post("/api/switches", data="{").status_code, 400)
        first, second = self.line(), self.line("W17")
        self.switch(first, asset_id="ASSET-001")
        self.switch(second, vendor="LYB", model="LB9", status="OFFLINE", hostname="SW-W17")
        for query in (f"production_line={first}", "status=OFFLINE", "vendor=LYB", "search=asset-001", "search=LB9", "search=SW-W17", f"production_line={second}&status=OFFLINE&vendor=LYB&search=LB9"):
            self.assertEqual(len(self.client.get(f"/api/switches?{query}").json), 1)
        self.assertEqual(self.client.get("/api/switches?search=%25").json, [])
        self.assertEqual(self.client.get("/api/switches?status=BAD").status_code, 400)
