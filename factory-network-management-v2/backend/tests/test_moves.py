from switch_fixtures import post_switch
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from app import create_app
from app.models import db, Switch, SwitchMoveHistory


class MoveTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (Path(self.directory.name) / "moves.db").as_posix()}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.source = self.client.post("/api/production-lines", json={"name": "H17"}).json["data"]["id"]
        self.target = self.client.post("/api/production-lines", json={"name": "A10"}).json["data"]["id"]
        self.record = post_switch(self.client, json=dict(hostname="S8ZE", vendor="LB9", model="LAN SW", asset_id="LB9-01", serial_number="77777", ip_address="172.19.0.8", block="H17-03", production_line_id=self.source, status="ACTIVE")).json["data"]
        self.url = f"/api/switches/{self.record['id']}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.directory.cleanup()

    def move(self, **changes):
        return self.client.post(self.url + "/move", json=dict(production_line_id=self.target, block="A10-01", hostname="S8A") | changes)

    def test_move_identity_counts_history_and_persistence(self):
        before = self.client.get("/api/dashboard").json
        response = self.move(notes="New fixture")
        self.assertEqual(response.status_code, 200)
        after = response.json["data"]
        for field in self.record:
            if field not in {"hostname", "production_line", "production_line_id", "block", "updated_at"}:
                self.assertEqual(after[field], self.record[field], field)
        self.assertEqual((after["hostname"], after["production_line"], after["block"]), ("S8A", "A10", "A10-01"))
        self.assertEqual(before, self.client.get("/api/dashboard").json)
        lines = {line["name"]: line for line in self.client.get("/api/production-lines").json}
        self.assertEqual((lines["H17"]["total_switches"], lines["H17"]["status"], lines["H17"]["switch_models"]), (0, "NO SWITCH", []))
        self.assertEqual((lines["A10"]["total_switches"], lines["A10"]["status"], lines["A10"]["switch_models"]), (1, "WORKING", ["LB9 LAN SW"]))
        history = self.client.get(self.url + "/moves").json
        self.assertEqual(len(history), 1)
        entry = history[0]
        self.assertEqual((entry["from_production_line_name"], entry["from_block"], entry["from_hostname"]), ("H17", "H17-03", "S8ZE"))
        self.assertEqual((entry["to_production_line_name"], entry["to_block"], entry["to_hostname"]), ("A10", "A10-01", "S8A"))
        self.assertEqual(entry["notes"], "New fixture")
        self.assertEqual(entry["moved_at"], after["updated_at"])
        self.assertEqual(datetime.fromisoformat(entry["moved_at"]).utcoffset(), timedelta(hours=7))
        self.client.patch(f"/api/production-lines/{self.source}", json={"name": "H18"})
        self.assertEqual(self.client.get(self.url + "/moves").json[0]["from_production_line_name"], "H17")
        second = create_app(self.config)
        self.assertEqual(second.test_client().get(self.url).json["hostname"], "S8A")
        self.assertEqual(second.test_client().get(self.url + "/moves").json, history)
        with second.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_same_line_and_no_change(self):
        response = self.move(production_line_id=self.source, block=" H17-03 ", hostname=" S8ZE ")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["message"], "No changes to move.")
        self.assertEqual(self.client.get(self.url).json, self.record)
        self.assertEqual(self.client.get(self.url + "/moves").json, [])
        self.assertEqual(self.move(production_line_id=self.source, block="H17-05", hostname="S8ZB").status_code, 200)
        self.assertEqual(len(self.client.get(self.url + "/moves").json), 1)

    def test_validation_and_deleted_guard(self):
        for changes in ({"hostname": " "}, {"hostname": "x" * 151}, {"block": "x" * 101}, {"production_line_id": 9999}, {"production_line_id": True}, {"production_line_id": "1"}, {"hostname": []}):
            self.assertEqual(self.move(**changes).status_code, 400)
        self.assertEqual(self.client.get(self.url).json, self.record)
        self.assertEqual(self.client.get(self.url + "/moves").json, [])
        with self.app.app_context():
            db.session.get(Switch, self.record["id"]).is_deleted = True
            db.session.commit()
        self.assertEqual(self.move().status_code, 400)
        self.assertEqual(self.client.post("/api/switches/9999/move", json={"hostname":"a", "production_line_id":self.target}).status_code, 404)

    def test_optional_block_and_unchanged_status_duplicate_ip(self):
        other = post_switch(self.client, json=dict(hostname="S8A", vendor="Arista", model="7060", production_line_id=self.target, status="OFFLINE", ip_address="172.19.0.8"))
        self.assertEqual(other.status_code, 201)
        for status in ("OFFLINE", "SPARE", "ACTIVE"):
            self.client.patch(self.url + "/status", json={"status": status})
            result = self.move(hostname=status, block=None)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json["data"]["status"], status)
            self.assertIsNone(result.json["data"]["block"])
        self.assertEqual(self.move(hostname="S8A").status_code, 200)  # Existing hostname rules allow duplicates.

    def test_source_remaining_offline_and_destination_status(self):
        post_switch(self.client, json=dict(hostname="remaining", vendor="Arista", model="7060", production_line_id=self.source, status="OFFLINE"))
        self.move()
        lines = {line["name"]: line for line in self.client.get("/api/production-lines").json}
        self.assertEqual(lines["H17"]["status"], "NOT WORKING")
        self.assertEqual(lines["A10"]["status"], "WORKING")

    def test_stale_review_rejected(self):
        self.client.patch(self.url + "/status", json={"status": "SPARE"})
        self.assertEqual(self.move(expected_updated_at=self.record["updated_at"]).status_code, 400)
        self.assertEqual(self.client.get(self.url + "/moves").json, [])

    def test_history_failure_rolls_back_switch(self):
        def fail(*args):
            raise SQLAlchemyError("Simulated history failure")
        event.listen(SwitchMoveHistory, "before_insert", fail)
        try:
            self.assertEqual(self.move().status_code, 503)
        finally:
            event.remove(SwitchMoveHistory, "before_insert", fail)
        self.assertEqual(self.client.get(self.url).json, self.record)
        self.assertEqual(self.client.get(self.url + "/moves").json, [])
