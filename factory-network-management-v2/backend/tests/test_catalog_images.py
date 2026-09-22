import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
from app import create_app
from app.models import db, SwitchCatalog


def picture(fmt="PNG", color="gray"):
    data = io.BytesIO()
    Image.new("RGB", (120, 40), color).save(data, format=fmt)
    return data.getvalue()


class CatalogImagesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "factory.db"
        self.config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + self.path.as_posix()}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.folder = self.app.config["CATALOG_IMAGE_DIR"]
        self.line = self.client.post("/api/production-lines", json={"name": "H17"}).json["data"]["id"]

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp.cleanup()

    def upload(self, name="Arista", fmt="PNG"):
        response = self.client.post("/api/switch-catalog", data={"name": name, "vendor": "Vendor", "model": name, "image": (io.BytesIO(picture(fmt)), "../../photo." + ("jpg" if fmt == "JPEG" else fmt.lower()))})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json["data"]

    def test_formats_and_safe_serving(self):
        for fmt in ("JPEG", "PNG", "WEBP"):
            entry = self.upload(fmt, fmt)
            self.assertRegex(entry["image_url"], r"^/api/media/switch-catalog/[0-9a-f]{32}\.webp$")
            self.assertNotIn("image_filename", entry)
            response = self.client.get(entry["image_url"])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            with Image.open(io.BytesIO(response.data)) as image:
                self.assertEqual(image.size, (120, 40))
                self.assertEqual(image.format, "WEBP")
            response.close()
        for path in ("../../factory.db", "%2e%2e%2ffactory.db", "factory.db", "a" * 32 + ".webp"):
            self.assertEqual(self.client.get("/api/media/switch-catalog/" + path).status_code, 404)
        self.assertEqual(len(list(self.folder.iterdir())), 3)

    def test_optional_and_invalid_replacement(self):
        empty = self.client.post("/api/switch-catalog", json={"name": "No image", "vendor": "V", "model": "M"}).json["data"]
        self.assertIsNone(empty["image_url"])
        entry = self.upload()
        url = f"/api/switch-catalog/{entry['id']}"
        for name, data in [("bad.exe", picture()), ("bad.zip", picture()), ("bad.svg", b"<svg/>"), ("fake.jpg", b"not an image"), ("big.png", b"x" * (5 * 1024 * 1024 + 1)), ("huge.png", b"x" * (7 * 1024 * 1024))]:
            response = self.client.patch(url, data={"image": (io.BytesIO(data), name)})
            self.assertIn(response.status_code, (400, 413))
            self.assertEqual(self.client.get(url).json, entry)
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        self.assertEqual(self.client.patch(url, data={"remove_image": "true", "image": (io.BytesIO(picture()), "a.png")}).status_code, 400)

    def test_replace_remove_and_failure_cleanup(self):
        entry = self.upload()
        url = f"/api/switch-catalog/{entry['id']}"
        old = self.folder / entry["image_url"].split("/")[-1]
        with patch("app.catalog_images.commit_record", side_effect=SQLAlchemyError("simulated commit failure")):
            response = self.client.patch(url, data={"image": (io.BytesIO(picture(color="blue")), "new.png")})
            self.assertEqual(response.status_code, 503)
        self.assertTrue(old.exists())
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        self.assertEqual(self.client.get(url).json, entry)
        with patch("pathlib.Path.open", side_effect=PermissionError("private server path")):
            response = self.client.patch(url, data={"image": (io.BytesIO(picture()), "new.png")})
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("private server path", response.json["message"])
        changed = self.client.patch(url, data={"image": (io.BytesIO(picture(color="blue")), "new.png")}).json["data"]
        self.assertNotEqual(entry["image_url"], changed["image_url"])
        self.assertFalse(old.exists())
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        removed = self.client.patch(url, data={"remove_image": "true"}, content_type="multipart/form-data").json["data"]
        self.assertIsNone(removed["image_url"])
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_shared_image_switch_edit_move_status_delete_restore(self):
        entry = self.upload()
        records = [self.client.post("/api/switches", json={"hostname": f"SW-{i}", "catalog_id": entry["id"], "production_line_id": self.line, "status": "ACTIVE"}).json["data"] for i in range(3)]
        self.assertTrue(all(row["catalog_image_url"] == entry["image_url"] for row in records))
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        before = self.client.get("/api/dashboard").json
        replacement = self.client.patch(f"/api/switch-catalog/{entry['id']}", data={"image": (io.BytesIO(picture(color="red")), "new.png")}).json["data"]
        self.assertTrue(all(row["catalog_image_url"] == replacement["image_url"] for row in self.client.get("/api/switches").json))
        self.assertEqual(self.client.get("/api/dashboard").json, before)
        record = records[0]; url = f"/api/switches/{record['id']}"
        target = self.client.post("/api/production-lines", json={"name": "A10"}).json["data"]["id"]
        self.client.post(url + "/move", json={"production_line_id": target, "hostname": "Moved", "block": "B01"})
        self.client.patch(url + "/status", json={"status": "OFFLINE"})
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})
        self.client.post("/api/switches/delete", json={"switch_ids": [record["id"]], "pin": "123456"})
        self.assertEqual(self.client.get(url).json["catalog_image_url"], replacement["image_url"])
        self.client.post("/api/switches/restore", json={"switch_ids": [record["id"]]})
        other = self.upload("LB9")
        changed = self.client.patch(url, json={"catalog_id": other["id"]}).json["data"]
        self.assertEqual(changed["catalog_image_url"], other["image_url"])
        self.assertEqual(changed["passport_uid"], record["passport_uid"])
        self.assertEqual(self.client.get("/api/passport/" + record["passport_uid"]).json["switch"]["catalog_image_url"], other["image_url"])

    def test_bulk_delete_cleans_only_unused_images(self):
        used, unused = self.upload("Used"), self.upload("Unused")
        record = self.client.post("/api/switches", json={"hostname": "SW", "catalog_id": used["id"], "production_line_id": self.line, "status": "ACTIVE"}).json["data"]
        self.client.post("/api/settings/delete-pin/setup", json={"new_pin": "123456", "confirm_pin": "123456"})
        self.client.post("/api/switches/delete", json={"switch_ids": [record["id"]], "pin": "123456"})
        payload = {"ids": [used["id"], unused["id"]], "pin": "111111"}
        self.assertEqual(self.client.post("/api/switch-catalog/delete", json=payload).status_code, 400)
        self.assertEqual(len(list(self.folder.iterdir())), 2)
        payload["pin"] = "123456"
        response = self.client.post("/api/switch-catalog/delete", json=payload).json
        self.assertEqual([row["id"] for row in response["deleted"]], [unused["id"]])
        self.assertEqual([row["id"] for row in response["blocked"]], [used["id"]])
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        self.assertTrue((self.folder / used["image_url"].split("/")[-1]).exists())

    def test_restart_missing_file_and_schema_upgrade(self):
        entry = self.upload()
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        restarted = create_app(self.config)
        response = restarted.test_client().get(entry["image_url"])
        self.assertEqual(response.status_code, 200); response.close()
        with restarted.app_context():
            db.session.remove(); db.engine.dispose()
        (self.folder / entry["image_url"].split("/")[-1]).unlink()
        self.assertEqual(self.client.get(entry["image_url"]).status_code, 404)
        self.assertEqual(self.client.get(f"/api/switch-catalog/{entry['id']}").status_code, 200)
        with self.app.app_context():
            db.session.remove(); db.engine.dispose()
        with sqlite3.connect(self.path) as conn:
            conn.execute("ALTER TABLE switch_catalog DROP COLUMN image_filename")
        conn.close()
        upgraded = create_app(self.config)
        result = upgraded.test_client().get(f"/api/switch-catalog/{entry['id']}").json
        self.assertEqual(result["id"], entry["id"])
        self.assertIsNone(result["image_url"])
        with upgraded.app_context():
            db.session.remove(); db.engine.dispose()
