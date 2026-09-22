import tempfile
import unittest
from pathlib import Path
from app import create_app
from app.models import db


class CatalogDeleteTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (Path(self.directory.name) / "test.db").as_posix()})
        self.client = self.app.test_client()
        self.line = self.client.post("/api/production-lines", json={"name": "A10"}).json["data"]["id"]
        self.entries = [self.client.post("/api/switch-catalog", json={"name": name, "vendor": "Test", "model": name}).json["data"] for name in ("Used", "IX7", "LB9", "Archived")]
        self.ids = [entry["id"] for entry in self.entries]
        self.record = self.client.post("/api/switches", json={"catalog_id": self.ids[0], "hostname": "S8A", "production_line_id": self.line, "status": "ACTIVE"}).json["data"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        self.directory.cleanup()

    def setup_pin(self):
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})

    def delete(self, ids, pin="123456"):
        return self.client.post("/api/switch-catalog/delete", json={"ids": ids, "pin": pin})

    def test_preview_and_mixed_delete_preserve_devices(self):
        self.setup_pin()
        before = self.client.get("/api/switches").json
        dashboard = self.client.get("/api/dashboard").json
        result = self.client.post("/api/switch-catalog/delete-preview", json={"ids": self.ids[:3]}).json
        self.assertEqual({r["id"] for r in result["eligible"]}, set(self.ids[1:3]))
        self.assertEqual(result["blocked"][0]["switch_count"], 1)
        result = self.delete(self.ids[:3])
        self.assertEqual(result.status_code, 200)
        self.assertEqual({r["id"] for r in result.json["deleted"]}, set(self.ids[1:3]))
        self.assertEqual([r["id"] for r in result.json["blocked"]], [self.ids[0]])
        self.assertEqual(self.client.get("/api/switches").json, before)
        self.assertEqual(self.client.get("/api/dashboard").json, dashboard)
        self.assertEqual(self.client.get(f"/api/switch-catalog/{self.ids[1]}").status_code, 404)

    def test_pin_required_wrong_format_and_wrong_pin(self):
        self.assertEqual(self.delete([self.ids[1]]).status_code, 400)
        self.setup_pin()
        for pin in ("111111", "12", 123456, None):
            self.assertEqual(self.delete([self.ids[1]], pin).status_code, 400)
            self.assertEqual(self.client.get(f"/api/switch-catalog/{self.ids[1]}").status_code, 200)
        self.assertEqual(self.delete([self.ids[1]]).json["deleted"][0]["id"], self.ids[1])

    def test_all_used_and_archived_models_blocked_and_restorable(self):
        self.setup_pin()
        archived = self.client.post("/api/switches", json={"catalog_id": self.ids[3], "hostname": "Archived", "production_line_id": self.line, "status": "SPARE"}).json["data"]
        self.client.post("/api/switches/delete", json={"switch_ids": [archived["id"]], "pin": "123456"})
        self.assertEqual(self.client.get(f"/api/switch-catalog/{self.ids[3]}").json["switch_count"], 0)
        result = self.delete([self.ids[0], self.ids[3]]).json
        self.assertEqual(result["deleted"], [])
        self.assertEqual(len(result["blocked"]), 2)
        self.assertTrue(any(r["deleted_switch_count"] == 1 for r in result["blocked"]))
        self.assertEqual(self.client.post("/api/switches/restore", json={"switch_ids": [archived["id"]]}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/switches/{archived['id']}").json["catalog_id"], self.ids[3])

    def test_usage_is_rechecked_after_preview(self):
        self.setup_pin()
        ids = self.ids[1:3]
        self.assertEqual(len(self.client.post("/api/switch-catalog/delete-preview", json={"ids": ids}).json["eligible"]), 2)
        self.client.post("/api/switches", json={"catalog_id": ids[0], "hostname": "New reference", "production_line_id": self.line, "status": "ACTIVE"})
        result = self.delete(ids).json
        self.assertEqual([r["id"] for r in result["deleted"]], [ids[1]])
        self.assertEqual([r["id"] for r in result["blocked"]], [ids[0]])

    def test_bad_ids_do_not_partially_delete(self):
        self.setup_pin()
        for ids in ([], [self.ids[1], 9999], [True], ["2"], [2, 2], "2", [-1]):
            self.assertEqual(self.delete(ids).status_code, 400)
            self.assertEqual(self.client.post("/api/switch-catalog/delete-preview", json={"ids": ids}).status_code, 400)
        self.assertEqual(len(self.client.get("/api/switch-catalog").json), 4)

    def test_existing_pin_change_applies_to_catalog(self):
        self.setup_pin()
        self.client.post("/api/settings/delete-pin/change", json={"current_pin": "123456", "new_pin": "654321", "confirm_pin": "654321"})
        self.assertEqual(self.delete([self.ids[1]]).status_code, 400)
        self.assertEqual(self.delete([self.ids[1]], "654321").status_code, 200)
