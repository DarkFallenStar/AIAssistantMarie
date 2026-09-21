import unittest
import asyncio
from starlette.testclient import TestClient
from app.main import app
from app.services.llm import MockLLMService
from app.services.webhook_extractor import BankWebhookExtractor
from app.api.endpoints.webhooks import set_webhook_extractor, set_transaction_tools
from app.tools.transaction_tool import TransactionTools


class TestBankWebhook(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.tx_tools = TransactionTools()
        set_transaction_tools(self.tx_tools)

    def tearDown(self):
        set_webhook_extractor(BankWebhookExtractor())
        set_transaction_tools(TransactionTools())

    def test_webhook_valid_purchase_with_structured_output(self):
        # Mock LLM returning structured JSON as expected
        mock_json_response = """{
            "amount": 45000.0,
            "currency": "COP",
            "merchant": "Comercio X",
            "date": "2026-09-21T10:30:00Z",
            "payment_method": "credit_card",
            "category": "food",
            "type": "expense"
        }"""
        mock_llm = MockLLMService(canned_response=mock_json_response)
        extractor = BankWebhookExtractor(llm_service=mock_llm)
        set_webhook_extractor(extractor)

        response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "bank",
                "content": "Compra realizada por $45.000 en Comercio X con tarjeta de crédito"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["transaction_id"])
        
        extracted = data["extracted"]
        self.assertEqual(extracted["amount"], 45000.0)
        self.assertEqual(extracted["currency"], "COP")
        self.assertEqual(extracted["merchant"], "Comercio X")
        self.assertEqual(extracted["payment_method"], "credit_card")
        self.assertEqual(extracted["category"], "food")
        self.assertEqual(extracted["type"], "expense")

        # Verify transaction persistence in storage
        created_tx = self.tx_tools._transactions[0]
        self.assertEqual(created_tx["id"], data["transaction_id"])
        self.assertEqual(created_tx["amount"], 45000.0)
        self.assertEqual(created_tx["currency"], "COP")
        self.assertEqual(created_tx["source"], "webhook_bank")
        self.assertEqual(created_tx["metadata"]["payment_method"], "credit_card")

    def test_webhook_heuristic_fallback_when_llm_fails(self):
        # LLM that fails/throws, triggering heuristic regex extractor
        class FailingLLM:
            async def generate(self, *args, **kwargs):
                raise RuntimeError("LLM connection timed out")

        extractor = BankWebhookExtractor(llm_service=FailingLLM())
        set_webhook_extractor(extractor)

        response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "bank",
                "content": "Compra realizada por $45.000 en Tienda D1 con tarjeta debito"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        extracted = data["extracted"]
        self.assertEqual(extracted["amount"], 45000.0)
        self.assertEqual(extracted["currency"], "COP")
        self.assertIn("Tienda D1", extracted["merchant"])
        self.assertEqual(extracted["payment_method"], "debit_card")
        self.assertEqual(extracted["category"], "food")
        self.assertEqual(extracted["type"], "expense")

    def test_webhook_income_transfer_notification(self):
        extractor = BankWebhookExtractor()  # uses heuristic or default
        set_webhook_extractor(extractor)

        response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "bank",
                "content": "Transferencia recibida por $120.000 de Pedro Perez"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        extracted = data["extracted"]
        self.assertEqual(extracted["amount"], 120000.0)
        self.assertEqual(extracted["type"], "income")

    def test_webhook_missing_source_rejected(self):
        response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "   ",
                "content": "Compra por $10.000"
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("source", response.json()["detail"].lower())

    def test_webhook_empty_content_rejected(self):
        response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "bank",
                "content": "   "
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("content", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
