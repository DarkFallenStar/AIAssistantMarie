import unittest
from starlette.testclient import TestClient
from app.main import app
from app.services.llm import MockLLMService, set_llm_service

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_llm = MockLLMService(canned_response="Hola, soy tu asistente.")
        set_llm_service(self.mock_llm)

    def tearDown(self):
        set_llm_service(None)

    def test_get_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_get_api_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_post_chat(self):
        payload = {"message": "Hola"}
        response = self.client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertEqual(data["response"], "Hola, soy tu asistente.")
        self.assertEqual(data["agent"], "GeneralOrchestrator")

    def test_post_chat_invalid_payload(self):
        response = self.client.post("/chat", json={})
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main()
