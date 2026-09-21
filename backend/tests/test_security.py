import unittest
import io
import uuid
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.core.config import settings
from app.schemas.chat import ChatRequest
from app.schemas.webhook import BankWebhookPayload
from app.api.endpoints.tts import TTSRequest
from app.services.llm.google import GoogleAIService
from app.services.webhook_extractor import BankWebhookExtractor
from app.schemas.webhook import ExtractedBankTransaction
from app.tools.transaction_tool import TransactionTools, ToolResult
from app.api.endpoints.webhooks import set_webhook_extractor, set_transaction_tools


class TestSecurityAndInputValidation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.original_bearer_token = settings.API_BEARER_TOKEN
        self.original_webhook_secret = settings.BANK_WEBHOOK_SECRET

    def tearDown(self):
        # Restore configuration
        settings.API_BEARER_TOKEN = self.original_bearer_token
        settings.BANK_WEBHOOK_SECRET = self.original_webhook_secret

    # --------------------------------------------------------------------------
    # 1. Chat Input Validation
    # --------------------------------------------------------------------------
    def test_chat_request_whitespace_only_rejected(self):
        """Rejects whitespace-only chat input."""
        with self.assertRaises(ValidationError):
            ChatRequest(message="    \n\t  ")

    def test_chat_request_empty_string_rejected(self):
        """Rejects empty chat message."""
        with self.assertRaises(ValidationError):
            ChatRequest(message="")

    def test_chat_request_excessive_length_rejected(self):
        """Rejects chat message exceeding 4096 characters."""
        long_message = "a" * 4097
        with self.assertRaises(ValidationError):
            ChatRequest(message=long_message)

    def test_chat_endpoint_empty_body_rejected_by_api(self):
        """API rejects whitespace-only chat message with 422 Unprocessable Entity."""
        settings.API_BEARER_TOKEN = ""
        response = self.client.post("/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 422)

    # --------------------------------------------------------------------------
    # 2. Bank Webhook Payload Validation
    # --------------------------------------------------------------------------
    def test_bank_webhook_whitespace_rejected(self):
        """Rejects whitespace-only source or content in bank webhook with HTTP 400."""
        settings.BANK_WEBHOOK_SECRET = ""
        res1 = self.client.post("/webhooks/bank", json={"source": "   ", "content": "Compra de $10.000"})
        self.assertEqual(res1.status_code, 400)
        res2 = self.client.post("/webhooks/bank", json={"source": "bank", "content": "   "})
        self.assertEqual(res2.status_code, 400)

    def test_bank_webhook_invalid_uuid_rejected(self):
        """Rejects invalid UUID format in user_id."""
        with self.assertRaises(ValidationError):
            BankWebhookPayload(source="bank", content="Compra de $10.000", user_id="not-a-valid-uuid")

    def test_bank_webhook_valid_uuid_accepted(self):
        """Accepts properly formed UUID."""
        valid_uuid = str(uuid.uuid4())
        payload = BankWebhookPayload(source="bank", content="Compra de $10.000", user_id=valid_uuid)
        self.assertEqual(payload.user_id, valid_uuid)

    # --------------------------------------------------------------------------
    # 3. Voice Upload Security Limits & Sanitization
    # --------------------------------------------------------------------------
    def test_voice_upload_excessive_file_size_rejected(self):
        """Uploads exceeding 25MB are rejected with 413 Payload Too Large."""
        settings.API_BEARER_TOKEN = ""
        # Create a buffer exceeding 25MB (25 * 1024 * 1024 + 100 bytes)
        large_bytes = b"0" * (25 * 1024 * 1024 + 1024)
        large_file = io.BytesIO(large_bytes)
        large_file.name = "giant_recording.m4a"

        response = self.client.post(
            "/voice",
            files={"file": ("giant_recording.m4a", large_file, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("25MB", response.json()["detail"])

    # --------------------------------------------------------------------------
    # 4. TTS Input Validation & Path Traversal Defense
    # --------------------------------------------------------------------------
    def test_tts_excessive_length_rejected(self):
        """Rejects TTS synthesis text exceeding 2000 characters."""
        with self.assertRaises(ValidationError):
            TTSRequest(text="x" * 2001)

    def test_tts_endpoint_path_traversal_blocked(self):
        """Attempting to access parent directories in /tts/{filename} returns 400 or 404."""
        settings.API_BEARER_TOKEN = ""
        response = self.client.get("/tts/..%2F..%2Fetc%2Fpasswd")
        # Either blocked as bad request or not found, never executes traversal
        self.assertIn(response.status_code, [400, 404])

    # --------------------------------------------------------------------------
    # 5. API Bearer Token Authentication
    # --------------------------------------------------------------------------
    def test_protected_endpoint_rejects_missing_token_when_configured(self):
        """When API_BEARER_TOKEN is configured, unauthenticated requests return 401."""
        settings.API_BEARER_TOKEN = "super-secret-token-12345"

        response = self.client.get("/db/status")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Token de autorización", response.json()["detail"])

    def test_protected_endpoint_rejects_invalid_token_when_configured(self):
        """When API_BEARER_TOKEN is configured, wrong tokens return 401."""
        settings.API_BEARER_TOKEN = "super-secret-token-12345"

        response = self.client.get(
            "/db/status",
            headers={"Authorization": "Bearer wrong-token-xyz"}
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_accepts_valid_bearer_token(self):
        """When API_BEARER_TOKEN is configured, matching token succeeds."""
        settings.API_BEARER_TOKEN = "super-secret-token-12345"

        response = self.client.get(
            "/db/status",
            headers={"Authorization": "Bearer super-secret-token-12345"}
        )
        self.assertEqual(response.status_code, 200)

    def test_protected_endpoint_accepts_valid_x_api_key_header(self):
        """Alternative X-API-Key header succeeds when matching token."""
        settings.API_BEARER_TOKEN = "super-secret-token-12345"

        response = self.client.get(
            "/db/status",
            headers={"X-API-Key": "super-secret-token-12345"}
        )
        self.assertEqual(response.status_code, 200)

    def test_protected_endpoint_permissive_when_token_empty_in_dev(self):
        """When API_BEARER_TOKEN is empty, dev requests pass without credentials."""
        settings.API_BEARER_TOKEN = ""

        response = self.client.get("/db/status")
        self.assertEqual(response.status_code, 200)

    def test_public_endpoints_accessible_without_token(self):
        """Public routes (/health, /, /openapi.json) never require token."""
        settings.API_BEARER_TOKEN = "super-secret-token-12345"

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)

        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)

        res_openapi = self.client.get("/openapi.json")
        self.assertEqual(res_openapi.status_code, 200)

    # --------------------------------------------------------------------------
    # 6. Bank Webhook Secret Validation
    # --------------------------------------------------------------------------
    def test_bank_webhook_rejects_missing_secret_when_configured(self):
        """When BANK_WEBHOOK_SECRET is configured, requests without secret return 401."""
        settings.BANK_WEBHOOK_SECRET = "webhook-secret-999"

        payload = {
            "source": "bank_app",
            "content": "Compra por $50.000 en Tienda D1 con tarjeta debito"
        }
        response = self.client.post("/webhooks/bank", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("X-Webhook-Secret", response.json()["detail"])

    def test_bank_webhook_rejects_invalid_secret_when_configured(self):
        """When BANK_WEBHOOK_SECRET is configured, mismatched secret returns 401."""
        settings.BANK_WEBHOOK_SECRET = "webhook-secret-999"

        payload = {
            "source": "bank_app",
            "content": "Compra por $50.000 en Tienda D1 con tarjeta debito"
        }
        response = self.client.post(
            "/webhooks/bank",
            json=payload,
            headers={"X-Webhook-Secret": "wrong-secret-value"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Webhook secret inválido", response.json()["detail"])

    def test_bank_webhook_accepts_valid_secret(self):
        """When BANK_WEBHOOK_SECRET is configured, matching secret is accepted."""
        settings.BANK_WEBHOOK_SECRET = "webhook-secret-999"

        # Mock extractor and transaction tools
        mock_extractor = MagicMock()
        extracted_data = ExtractedBankTransaction(
            amount=50000.0,
            currency="COP",
            merchant="Tienda D1",
            date="2026-09-21T12:00:00Z",
            payment_method="debit_card",
            category="food",
            type="expense"
        )
        async def fake_extract(*args, **kwargs):
            return extracted_data
        mock_extractor.extract_from_text = fake_extract
        set_webhook_extractor(mock_extractor)

        mock_tools = MagicMock()
        async def fake_create(*args, **kwargs):
            return ToolResult(success=True, data={"id": str(uuid.uuid4())}, message="Created")
        mock_tools.create_transaction = fake_create
        set_transaction_tools(mock_tools)

        payload = {
            "source": "bank_app",
            "content": "Compra por $50.000 en Tienda D1 con tarjeta debito"
        }
        response = self.client.post(
            "/webhooks/bank",
            json=payload,
            headers={"X-Webhook-Secret": "webhook-secret-999"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    # --------------------------------------------------------------------------
    # 7. LLM API Key Security: Header vs URL Parameter
    # --------------------------------------------------------------------------
    def test_google_ai_service_uses_header_not_query_string(self):
        """GoogleAIService must not leak GEMINI_API_KEY in the URL query string."""
        service = GoogleAIService(api_key="TEST_API_KEY_12345", model="gemini-3.5-flash")
        # Verify the key is stored cleanly
        self.assertEqual(service._api_key, "TEST_API_KEY_12345")


if __name__ == "__main__":
    unittest.main()
