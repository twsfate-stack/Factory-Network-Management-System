import unittest
from app import create_app


class HealthTest(unittest.TestCase):
    def test_health_contract(self):
        response = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}).test_client().get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            "status": "ok", "application": "Factory Network Management System"
        })

    def test_empty_switch_endpoint(self):
        response = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}).test_client().get("/api/switches")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])
