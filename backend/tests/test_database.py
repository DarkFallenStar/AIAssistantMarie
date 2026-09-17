import unittest
from starlette.testclient import TestClient
from app.main import app

class TestDatabaseEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_db_status(self):
        response = self.client.get("/db/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("connected", data)
        self.assertIn("tables_defined", data)
        
        # Verify that all 8 required tables are tracked in the database configuration
        expected_tables = [
            "users", "tasks", "emails", "financial_accounts",
            "credit_cards", "loans", "saving_goals", "transactions"
        ]
        for table in expected_tables:
            self.assertIn(table, data["tables_defined"])

    def test_get_api_db_status(self):
        response = self.client.get("/api/db/status")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
