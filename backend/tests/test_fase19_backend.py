import unittest
import asyncio
from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.agents.orchestrator import get_orchestrator_service
from app.services.llm.mock import MockLLMService
from app.api.endpoints.webhooks import set_webhook_extractor
from app.services.webhook_extractor import BankWebhookExtractor

class TestFase19Backend(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_llm = MockLLMService(canned_response="Hola, soy tu asistente personal listo para ayudarte.")
        self.orchestrator = get_orchestrator_service()
        self.orchestrator.set_llm_service(self.mock_llm)
        self.extractor = BankWebhookExtractor(llm_service=self.mock_llm)
        set_webhook_extractor(self.extractor)

    def tearDown(self):
        self.orchestrator.set_llm_service(None)
        set_webhook_extractor(BankWebhookExtractor())

    # -------------------------------------------------------------
    # 1. GET /health
    # -------------------------------------------------------------
    def test_get_health_root(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_get_health_api_prefix(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    # -------------------------------------------------------------
    # 2. POST /chat
    # -------------------------------------------------------------
    def test_post_chat_valid_message(self):
        headers = {}
        if settings.API_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.API_BEARER_TOKEN}"
        
        response = self.client.post("/chat", json={"message": "Hola, ¿cómo estás?"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("intent", data)
        self.assertIn("agent", data)
        self.assertIn("tools_executed", data)
        self.assertIsInstance(data["tools_executed"], list)

    def test_post_chat_empty_message_validation(self):
        headers = {}
        if settings.API_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.API_BEARER_TOKEN}"

        # Empty string should fail validation
        res_empty = self.client.post("/chat", json={"message": ""}, headers=headers)
        self.assertEqual(res_empty.status_code, 422)

        # Whitespace-only string should fail validation
        res_whitespace = self.client.post("/chat", json={"message": "    "}, headers=headers)
        self.assertEqual(res_whitespace.status_code, 422)

    def test_post_chat_max_length_validation(self):
        headers = {}
        if settings.API_BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {settings.API_BEARER_TOKEN}"

        huge_message = "x" * 4097
        response = self.client.post("/chat", json={"message": huge_message}, headers=headers)
        self.assertEqual(response.status_code, 422)

    def test_post_chat_auth_protection(self):
        orig_token = settings.API_BEARER_TOKEN
        try:
            settings.API_BEARER_TOKEN = "super_secret_token_123"
            # Without token -> 401
            res_no_auth = self.client.post("/chat", json={"message": "Mensaje de prueba"})
            self.assertEqual(res_no_auth.status_code, 401)

            # With wrong token -> 401
            res_bad_auth = self.client.post("/chat", json={"message": "Mensaje de prueba"}, headers={"Authorization": "Bearer wrong_token"})
            self.assertEqual(res_bad_auth.status_code, 401)

            # With valid token -> 200
            res_good_auth = self.client.post("/chat", json={"message": "Mensaje de prueba"}, headers={"Authorization": "Bearer super_secret_token_123"})
            self.assertEqual(res_good_auth.status_code, 200)
        finally:
            settings.API_BEARER_TOKEN = orig_token

    # -------------------------------------------------------------
    # 3. POST /webhooks/bank
    # -------------------------------------------------------------
    def test_post_bank_webhook_valid_payload(self):
        mock_json = """{
            "amount": 65000.0,
            "currency": "COP",
            "merchant": "Supermercado Éxito",
            "date": "2026-09-21T10:30:00Z",
            "payment_method": "credit_card",
            "category": "supermercado",
            "type": "expense"
        }"""
        set_webhook_extractor(BankWebhookExtractor(llm_service=MockLLMService(canned_response=mock_json)))

        headers = {}
        if settings.BANK_WEBHOOK_SECRET:
            headers["X-Webhook-Secret"] = settings.BANK_WEBHOOK_SECRET

        payload = {
            "source": "macrodroid",
            "content": "Bancolombia le informa compra con tarjeta terminada en 4321 por $65.000 en Supermercado Éxito el 21/09/2026."
        }
        response = self.client.post("/webhooks/bank", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("transaction_id", data)
        self.assertIn("extracted", data)
        self.assertEqual(data["extracted"]["amount"], 65000.0)
        self.assertIn("Supermercado", data["extracted"]["merchant"])

    def test_post_bank_webhook_heuristic_fallback(self):
        # Test purely heuristic regex extraction when LLM fails or is offline
        class FailingLLM:
            async def generate(self, *args, **kwargs):
                raise RuntimeError("LLM offline simulation")

        set_webhook_extractor(BankWebhookExtractor(llm_service=FailingLLM()))
        headers = {}
        if settings.BANK_WEBHOOK_SECRET:
            headers["X-Webhook-Secret"] = settings.BANK_WEBHOOK_SECRET

        payload = {
            "source": "macrodroid",
            "content": "Bancolombia le informa compra con tarjeta terminada en 4321 por $65.000 en Supermercado Éxito el 21/09/2026."
        }
        response = self.client.post("/webhooks/bank", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["extracted"]["amount"], 65000.0)
        self.assertIn("Supermercado", data["extracted"]["merchant"])

    def test_post_bank_webhook_secret_protection(self):
        orig_secret = settings.BANK_WEBHOOK_SECRET
        try:
            settings.BANK_WEBHOOK_SECRET = "webhook_guard_secret_777"
            # Without secret -> 401
            payload = {"source": "macrodroid", "content": "Compra por $20.000 en Farmacia"}
            res_no_sec = self.client.post("/webhooks/bank", json=payload)
            self.assertEqual(res_no_sec.status_code, 401)

            # With wrong secret -> 401
            res_bad_sec = self.client.post("/webhooks/bank", json=payload, headers={"X-Webhook-Secret": "invalid_secret"})
            self.assertEqual(res_bad_sec.status_code, 401)

            # With correct secret -> 200
            res_good_sec = self.client.post("/webhooks/bank", json=payload, headers={"X-Webhook-Secret": "webhook_guard_secret_777"})
            self.assertEqual(res_good_sec.status_code, 200)
        finally:
            settings.BANK_WEBHOOK_SECRET = orig_secret

    def test_post_bank_webhook_query_sync(self):
        mock_json = """{
            "amount": 48500.0,
            "currency": "COP",
            "merchant": "Gasolinera Primax",
            "date": "2026-09-21T10:30:00Z",
            "payment_method": "credit_card",
            "category": "transporte",
            "type": "expense"
        }"""
        set_webhook_extractor(BankWebhookExtractor(llm_service=MockLLMService(canned_response=mock_json)))

        headers = {}
        if settings.BANK_WEBHOOK_SECRET:
            headers["X-Webhook-Secret"] = settings.BANK_WEBHOOK_SECRET
        auth_headers = {}
        if settings.API_BEARER_TOKEN:
            auth_headers["Authorization"] = f"Bearer {settings.API_BEARER_TOKEN}"

        payload = {
            "source": "android_notification",
            "content": "Banco Davivienda: Compra por $48.500 en Gasolinera Primax."
        }
        wh_res = self.client.post("/webhooks/bank", json=payload, headers=headers)
        self.assertEqual(wh_res.status_code, 200)
        tx_id = wh_res.json()["transaction_id"]

        # Verify recent transactions endpoint exposes it
        recent_res = self.client.get("/webhooks/bank/recent?limit=10", headers=auth_headers)
        self.assertEqual(recent_res.status_code, 200)
        recent_data = recent_res.json()
        ids = [t["id"] for t in recent_data["transactions"]]
        self.assertIn(tx_id, ids)

if __name__ == "__main__":
    unittest.main()
