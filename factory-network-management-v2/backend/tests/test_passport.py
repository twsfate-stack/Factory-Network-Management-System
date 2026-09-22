from switch_fixtures import post_switch
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from uuid import UUID, uuid4
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.models import db, Switch
from app.routes.passport import validate_public_base_url


class PassportTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "passport.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + self.path.as_posix(), "PUBLIC_BASE_URL": "http://fnms.company.local"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.source = self.client.post("/api/production-lines", json={"name": "H17"}).json["data"]["id"]
        self.target = self.client.post("/api/production-lines", json={"name": "A10"}).json["data"]["id"]
        self.record = post_switch(self.client, json=dict(hostname="S8ZE", vendor="LB9", model="LAN SW", asset_id="LB9-01", serial_number="77777", ip_address="172.19.0.8", block="H17-03", production_line_id=self.source, status="ACTIVE", passport_uid="client-controlled")).json["data"]
        self.uid = self.record["passport_uid"]
        self.url = "/api/passport/" + self.uid
        self.switch_url = f"/api/switches/{self.record['id']}"

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.directory.cleanup()

    def test_public_identity_api_and_qr(self):
        self.assertEqual(UUID(self.uid).version, 4)
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        self.assertEqual(result.json["passport_url"], "http://fnms.company.local/passport/" + self.uid)
        self.assertEqual(result.json["switch"]["hostname"], "S8ZE")
        self.assertEqual(result.json["history"], [])
        self.assertTrue(result.json["switch"]["created_at"].endswith("+07:00"))
        self.assertNotIn("id", result.json["switch"])
        self.assertEqual(set(result.json), {"passport_uid", "switch", "history", "has_more_history", "passport_url"})
        import segno
        with patch("app.routes.passport.segno.make_qr", wraps=segno.make_qr) as make:
            qr = self.client.get(self.url + "/qr.png?download=1")
            make.assert_called_once_with(result.json["passport_url"], error="m")
        self.assertEqual(qr.status_code, 200)
        self.assertEqual(qr.mimetype, "image/png")
        self.assertTrue(qr.data.startswith(bytes([137, 80, 78, 71, 13, 10, 26, 10])))
        self.assertIn("attachment", qr.headers["Content-Disposition"])
        self.assertEqual(self.client.get("/api/passport/not-a-uuid").status_code, 404)
        self.assertEqual(self.client.get("/api/passport/" + str(uuid4())).status_code, 404)
        self.assertEqual(self.client.post(self.url, json={"status": "SPARE"}).status_code, 405)

    def test_move_status_soft_delete_restore_and_restart(self):
        qr = self.client.get(self.url + "/qr.png").data
        move = self.client.post(self.switch_url + "/move", json=dict(hostname="S8A", block="A10-01", production_line_id=self.target))
        self.assertEqual(move.status_code, 200)
        result = self.client.get(self.url).json
        self.assertEqual(result["passport_uid"], self.uid)
        self.assertEqual((result["switch"]["production_line"], result["switch"]["block"], result["switch"]["hostname"]), ("A10", "A10-01", "S8A"))
        self.assertEqual(result["history"][0]["from_production_line_name"], "H17")
        self.assertEqual(result["history"][0]["to_hostname"], "S8A")
        self.client.patch(self.switch_url + "/status", json={"status": "SPARE"})
        self.assertEqual(self.client.get(self.url).json["switch"]["status"], "SPARE")
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})
        self.assertEqual(self.client.post("/api/switches/delete", json={"switch_ids": [self.record["id"]], "pin": "123456"}).status_code, 200)
        self.assertTrue(self.client.get(self.url).json["switch"]["is_deleted"])
        self.assertEqual(self.client.post("/api/switches/restore", json={"switch_ids": [self.record["id"]]}).status_code, 200)
        second = create_app(self.config)
        self.assertEqual(second.test_client().get(self.url).json["passport_uid"], self.uid)
        self.assertEqual(second.test_client().get(self.url + "/qr.png").data, qr)
        self.assertEqual(second.test_client().get(self.url).json["switch"]["created_at"], self.record["created_at"])
        with second.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_identity_immutable_and_unique(self):
        with self.app.app_context():
            record = db.session.get(Switch, self.record["id"])
            record.passport_uid = str(uuid4())
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            duplicate = Switch(passport_uid=self.uid, hostname="Other", vendor="Arista", model="7060", production_line_id=self.source, status="ACTIVE")
            db.session.add(duplicate)
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
        self.assertEqual(self.client.get(self.url).json["passport_uid"], self.uid)

    def test_recent_history_limit_and_snapshots(self):
        for index in range(12):
            self.assertEqual(self.client.post(self.switch_url + "/move", json=dict(hostname=f"SW-{index}", block=str(index), production_line_id=self.target)).status_code, 200)
        self.client.patch(f"/api/production-lines/{self.target}", json={"name": "A11"})
        result = self.client.get(self.url).json
        self.assertEqual(len(result["history"]), 10)
        self.assertTrue(result["has_more_history"])
        self.assertEqual(result["history"][0]["to_hostname"], "SW-11")
        self.assertEqual(result["history"][0]["to_production_line_name"], "A10")
        self.assertEqual(result["switch"]["production_line"], "A11")

    def test_existing_active_and_deleted_backfill_once(self):
        second = post_switch(self.client, json=dict(hostname="Archived", vendor="Arista", model="7060", production_line_id=self.source, status="OFFLINE")).json["data"]
        with self.app.app_context():
            db.session.get(Switch, second["id"]).is_deleted = True
            db.session.commit()
            db.session.remove()
            db.engine.dispose()
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("DROP TRIGGER passport_uid_required")
            connection.execute("DROP TRIGGER passport_uid_immutable")
            connection.execute("DROP INDEX ux_switches_passport_uid")
            connection.execute("ALTER TABLE switches DROP COLUMN passport_uid")
            connection.commit()
            columns = [r[1] for r in connection.execute("PRAGMA table_info(switches)")]
            before = connection.execute("SELECT * FROM switches ORDER BY id").fetchall()
        uids = None
        for _ in range(2):
            upgraded = create_app(self.config)
            with upgraded.app_context():
                db.session.remove()
                db.engine.dispose()
            with closing(sqlite3.connect(self.path)) as connection:
                self.assertEqual(connection.execute("SELECT " + ",".join(columns) + " FROM switches ORDER BY id").fetchall(), before)
                current = connection.execute("SELECT passport_uid FROM switches ORDER BY id").fetchall()
                self.assertEqual(len({r[0] for r in current}), 2)
                self.assertTrue(all(UUID(r[0]).version == 4 for r in current))
                if uids is not None:
                    self.assertEqual(current, uids)
                uids = current
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_unconfigured_qr_and_config_validation(self):
        self.app.config["PUBLIC_BASE_URL"] = ""
        self.assertIsNone(self.client.get(self.url).json["passport_url"])
        self.assertEqual(self.client.get(self.url + "/qr.png").status_code, 503)
        for invalid in ("javascript:alert(1)", "http://user:secret@host", "http://host/#/x", "http://host/api", "http://host?a=1", "http://host:invalid", "http://bad host"):
            with self.assertRaises(ValueError):
                validate_public_base_url(invalid)
        self.assertEqual(validate_public_base_url("http://fnms.company.local/"), "http://fnms.company.local")
