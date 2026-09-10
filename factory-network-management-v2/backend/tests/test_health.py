import unittest
from app import create_app


class HealthTest(unittest.TestCase):
    def test_health_contract(self):
        response = create_app().test_client().get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            "status": "ok", "application": "Factory Network Management System"
        })

    def test_business_endpoint_does_not_exist(self):
        self.assertEqual(create_app().test_client().get("/api/switches").status_code, 404)
