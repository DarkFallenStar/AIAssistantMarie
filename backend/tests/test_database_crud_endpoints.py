import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import is_valid_uuid

class TestDatabaseCrudEndpoints(unittest.TestCase):
    """
    Tests generic CRUD database endpoints (/db/summary, /db/table/{table_name}, POST, PATCH, DELETE).
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_get_db_summary(self):
        response = self.client.get("/db/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("counts", data)
        self.assertIn("tasks", data["counts"])
        self.assertIn("transactions", data["counts"])

    def test_list_table_records(self):
        # Test tasks
        response = self.client.get("/db/table/tasks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success" if data["status"] == "success" else "in_memory_fallback")
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)

        # Test transactions
        response_tx = self.client.get("/db/table/transactions")
        self.assertEqual(response_tx.status_code, 200)
        data_tx = response_tx.json()
        self.assertIn("data", data_tx)

    def test_crud_task_lifecycle(self):
        # 1. Create a task manually via POST
        create_payload = {
            "title": "Tarea de prueba CRUD manual",
            "description": "Creada desde endpoint CRUD",
            "priority": "high",
            "category": "general"
        }
        res_create = self.client.post("/db/table/tasks", json=create_payload)
        self.assertEqual(res_create.status_code, 200)
        created_data = res_create.json()["data"]
        task_id = created_data["id"]
        self.assertTrue(is_valid_uuid(task_id))
        self.assertEqual(created_data["title"], "Tarea de prueba CRUD manual")

        # 2. Update the task via PATCH
        update_payload = {
            "status": "completed",
            "description": "Descripción actualizada vía PATCH"
        }
        res_update = self.client.patch(f"/db/table/tasks/{task_id}", json=update_payload)
        self.assertEqual(res_update.status_code, 200)
        updated_data = res_update.json()["data"]
        self.assertEqual(updated_data.get("status"), "completed")

        # 3. Delete the task via DELETE
        res_delete = self.client.delete(f"/db/table/tasks/{task_id}")
        self.assertEqual(res_delete.status_code, 200)
        del_data = res_delete.json()
        self.assertEqual(del_data["status"], "deleted")
        self.assertEqual(del_data["id"], task_id)

    def test_crud_transaction_manual(self):
        # 1. Create a transaction
        tx_payload = {
            "type": "expense",
            "amount": 25000.0,
            "category": "alimentacion",
            "description": "Almuerzo ejecutivo en restaurante",
            "merchant": "Restaurante Central"
        }
        res_create = self.client.post("/db/table/transactions", json=tx_payload)
        self.assertEqual(res_create.status_code, 200)
        created = res_create.json()["data"]
        tx_id = created["id"]
        self.assertTrue(is_valid_uuid(tx_id))
        self.assertEqual(created["currency"], "COP")

        # 2. Delete the transaction
        res_delete = self.client.delete(f"/db/table/transactions/{tx_id}")
        self.assertEqual(res_delete.status_code, 200)

    def test_invalid_table_name_raises_400(self):
        response = self.client.get("/db/table/non_existent_table")
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
