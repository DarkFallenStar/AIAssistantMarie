import unittest
import io
import asyncio
from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.audio.stt import MockSTTService, set_stt_service
from app.audio.tts import MockTTSService, set_tts_service
from app.services.llm import MockLLMService, set_llm_service, FailoverLLMService
from app.services.webhook_extractor import BankWebhookExtractor
from app.api.endpoints.webhooks import set_webhook_extractor, set_transaction_tools
from app.tools.transaction_tool import TransactionTools
from app.agents.orchestrator import get_orchestrator_service
from app.tools.task_tool import TaskTools
from app.tools.email_tool import EmailTools


class TestPhase18FullIntegration(unittest.TestCase):
    """
    Fase 18 — Integración Completa
    Verifica la unificación integral de todos los módulos:
    1. Mobile App -> Voice -> Backend -> Orchestrator -> Secretary/Financial -> Database -> TTS
    2. Bank Notification -> Webhook -> Financial Agent -> Database
    3. Human-in-the-loop Email Confirmation Flow
    4. Security & Authentication across all integrated endpoints
    5. Dual Failover LLM Resilience in integrated pipeline
    """

    def setUp(self):
        self.client = TestClient(app)
        self.original_bearer_token = settings.API_BEARER_TOKEN
        self.original_webhook_secret = settings.BANK_WEBHOOK_SECRET
        
        # Reset storage and tools to clean baseline
        TransactionTools.reset_mock_data()
        self.tx_tools = TransactionTools()
        set_transaction_tools(self.tx_tools)
        
        self.mock_tts = MockTTSService()
        set_tts_service(self.mock_tts)
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(None)

    def tearDown(self):
        settings.API_BEARER_TOKEN = self.original_bearer_token
        settings.BANK_WEBHOOK_SECRET = self.original_webhook_secret
        set_stt_service(None)
        set_tts_service(None)
        set_llm_service(None)
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(None)
        orchestrator._pending_confirmation = None
        set_webhook_extractor(BankWebhookExtractor())
        set_transaction_tools(TransactionTools())
        TransactionTools.reset_mock_data()

    # =========================================================================
    # Test 1: Flow A - Voice -> STT -> Orchestrator -> SecretaryAgent -> DB -> TTS
    # =========================================================================
    def test_voice_to_secretary_agent_end_to_end(self):
        """
        Usuario graba un audio pidiendo crear una tarea urgente.
        Backend transcribe audio (STT), Orquestador clasifica a SecretaryAgent,
        ejecuta create_task, persiste la tarea, sintetiza respuesta con TTS
        y devuelve VoiceUploadResponse con la URL del audio.
        """
        task_instruction = "Anota una tarea urgente para entregar el reporte mensual mañana"
        set_stt_service(MockSTTService(task_instruction))

        # Canned LLM function calling output
        mock_function_call = """{
            "agent": "secretary",
            "tool": "create_task",
            "arguments": {
                "title": "Entregar el reporte mensual",
                "due_date": "mañana",
                "priority": "high"
            },
            "reasoning": "El usuario solicita crear una tarea urgente para entregar el reporte"
        }"""
        mock_llm = MockLLMService(canned_response=mock_function_call)
        set_llm_service(mock_llm)
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(mock_llm)

        fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....voice_secretary_bytes")
        fake_audio.name = "audio_secretary.m4a"

        response = self.client.post(
            "/voice",
            files={"file": ("audio_secretary.m4a", fake_audio, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verificaciones de integración
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["transcribed_text"], task_instruction)
        self.assertEqual(data["intent"], "secretary")
        self.assertTrue(data["response"])
        self.assertIsNotNone(data["audio_url"])
        self.assertTrue(data["audio_url"].startswith("/static/audio/tts/"))

    # =========================================================================
    # Test 2: Flow A - Voice -> STT -> Orchestrator -> FinancialAgent -> DB -> TTS
    # =========================================================================
    def test_voice_to_financial_agent_end_to_end(self):
        """
        Usuario graba un audio registrando un gasto.
        Backend transcribe audio (STT), Orquestador clasifica a FinancialAgent,
        ejecuta create_transaction, persiste en DB, sintetiza respuesta con TTS.
        """
        financial_instruction = "Registra un gasto de 55 dólares en supermercado"
        set_stt_service(MockSTTService(financial_instruction))

        mock_function_call = """{
            "agent": "financial",
            "tool": "create_transaction",
            "arguments": {
                "amount": 55.0,
                "type": "expense",
                "category": "supermercado",
                "description": "Compra en supermercado",
                "merchant": "Supermercado"
            },
            "reasoning": "El usuario solicita registrar un gasto en supermercado"
        }"""
        mock_llm = MockLLMService(canned_response=mock_function_call)
        set_llm_service(mock_llm)
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(mock_llm)

        fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....voice_financial_bytes")
        fake_audio.name = "audio_financial.m4a"

        response = self.client.post(
            "/voice",
            files={"file": ("audio_financial.m4a", fake_audio, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["transcribed_text"], financial_instruction)
        self.assertEqual(data["intent"], "financial")
        self.assertIsNotNone(data["audio_url"])

        # Verificar que la transacción quedó guardada en el almacenamiento
        saved_txs = asyncio.run(self.tx_tools.get_transactions(category="supermercado"))
        self.assertTrue(saved_txs.success)
        self.assertTrue(any(t.get("amount") == 55.0 for t in saved_txs.data["transactions"]))

    # =========================================================================
    # Test 3: Flow B - Bank Notification -> Webhook -> Financial Agent Query
    # =========================================================================
    def test_parallel_bank_notification_webhook_to_financial_agent(self):
        """
        Verifica el flujo paralelo completo:
        1. Se recibe una notificación bancaria pasiva vía Webhook (POST /webhooks/bank).
        2. El webhook extrae la información y registra la transacción en la base de datos.
        3. Inmediatamente el usuario consulta al Asistente (vía /chat o /voice):
           '¿Cuáles fueron mis últimas transacciones?' o '¿Cuánto dinero he gastado?'
        4. El FinancialAgent lee la base de datos y la transacción del webhook
           aparece inmediatamente en el cálculo y en el listado.
        """
        # Paso 1: Configurar extractor mock para la notificación bancaria
        webhook_json = """{
            "amount": 89.90,
            "currency": "USD",
            "merchant": "Restaurante El Corral",
            "date": "2026-09-21T13:00:00Z",
            "payment_method": "tarjeta de debito",
            "category": "restaurante",
            "type": "expense"
        }"""
        mock_llm_webhook = MockLLMService(canned_response=webhook_json)
        extractor = BankWebhookExtractor(llm_service=mock_llm_webhook)
        set_webhook_extractor(extractor)

        webhook_response = self.client.post(
            "/webhooks/bank",
            json={
                "source": "android_notification_listener",
                "content": "Compra aprobada por $89.90 en Restaurante El Corral con tu tarjeta debito"
            }
        )
        self.assertEqual(webhook_response.status_code, 200)
        webhook_data = webhook_response.json()
        self.assertEqual(webhook_data["status"], "success")
        created_tx_id = webhook_data["transaction_id"]
        self.assertTrue(created_tx_id)

        # Paso 2: Consulta al Asistente pidiendo los últimos movimientos
        query_function_call = """{
            "agent": "financial",
            "tool": "list_transactions",
            "arguments": {
                "limit": 5
            },
            "reasoning": "El usuario solicita consultar sus transacciones recientes"
        }"""
        mock_llm_chat = MockLLMService(canned_response=query_function_call)
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(mock_llm_chat)

        chat_response = self.client.post(
            "/chat",
            json={"message": "¿Cuáles fueron mis últimas transacciones?"}
        )
        self.assertEqual(chat_response.status_code, 200)
        chat_data = chat_response.json()

        self.assertEqual(chat_data["intent"], "financial")
        self.assertEqual(chat_data["agent"], "FinancialAgent")
        self.assertIn("list_transactions", chat_data["tools_executed"])

        # Paso 3: Verificar que la transacción del webhook existe en la consulta de TransactionTools
        recent_txs = asyncio.run(self.tx_tools.get_transactions(limit=5))
        self.assertTrue(recent_txs.success)
        matching_tx = next((t for t in recent_txs.data["transactions"] if t["id"] == created_tx_id), None)
        self.assertIsNotNone(matching_tx, "La transacción recibida por webhook debe estar presente en el historial financiero.")
        self.assertEqual(matching_tx["merchant"], "Restaurante El Corral")
        self.assertEqual(matching_tx["amount"], 89.90)

    # =========================================================================
    # Test 4: Human-in-the-Loop Email Confirmation in Integrated Flow
    # =========================================================================
    def test_secretary_email_human_in_the_loop_integrated_flow(self):
        """
        Verifica el flujo con salvaguarda humana (Fase 12):
        1. Petición para enviar correo -> sistema crea borrador y solicita confirmación.
        2. El usuario responde 'Sí, confirmo' -> el correo se envía formalmente.
        """
        orchestrator = get_orchestrator_service()

        # Paso 1: Petición de envío de email
        send_email_json = """{
            "agent": "secretary",
            "tool": "send_email",
            "arguments": {
                "recipient": "director@universidad.edu",
                "subject": "Avance de Tesis",
                "body": "Estimado director, le adjunto el informe de avance."
            },
            "reasoning": "El usuario solicita enviar un correo"
        }"""
        mock_llm = MockLLMService(canned_response=send_email_json)
        orchestrator.set_llm_service(mock_llm)

        resp1 = self.client.post(
            "/chat",
            json={"message": "Envía un correo a director@universidad.edu con asunto Avance de Tesis"}
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertIn("send_email", data1["tools_executed"])
        self.assertIn("confirm", data1["response"].lower())
        self.assertIsNotNone(orchestrator._pending_confirmation)

        # Paso 2: Usuario confirma el envío
        resp2 = self.client.post(
            "/chat",
            json={"message": "Sí, confirmo el envío del correo"}
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertIn("enviado exitosamente", data2["response"].lower())
        self.assertIsNone(orchestrator._pending_confirmation)

    # =========================================================================
    # Test 5: Security & Authentication Enforcement Across All Endpoints
    # =========================================================================
    def test_security_enforcement_in_integrated_pipeline(self):
        """
        Verifica que los encabezados de seguridad (Bearer Token & Webhook Secret)
        se apliquen en todos los endpoints protegidos del sistema integrado.
        """
        settings.API_BEARER_TOKEN = "secret_token_12345"
        settings.BANK_WEBHOOK_SECRET = "webhook_secret_67890"

        # 1. /chat sin token -> 401
        r_chat_unauth = self.client.post("/chat", json={"message": "Hola"})
        self.assertEqual(r_chat_unauth.status_code, 401)

        # 2. /chat con token válido -> 200
        mock_llm = MockLLMService(canned_response="Hola, estoy a tu servicio.")
        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(mock_llm)
        r_chat_auth = self.client.post(
            "/chat",
            json={"message": "Hola"},
            headers={"Authorization": "Bearer secret_token_12345"}
        )
        self.assertEqual(r_chat_auth.status_code, 200)

        # 3. /voice sin token -> 401
        fake_audio = io.BytesIO(b"RIFF....data")
        r_voice_unauth = self.client.post(
            "/voice",
            files={"file": ("test.m4a", fake_audio, "audio/m4a")}
        )
        self.assertEqual(r_voice_unauth.status_code, 401)

        # 4. /webhooks/bank sin secret -> 401
        r_wh_unauth = self.client.post(
            "/webhooks/bank",
            json={"source": "test", "content": "test notification"}
        )
        self.assertEqual(r_wh_unauth.status_code, 401)

        # 5. /health es público -> 200 sin auth
        r_health = self.client.get("/health")
        self.assertEqual(r_health.status_code, 200)

    # =========================================================================
    # Test 6: Dual LLM Failover Resilience in Integrated Flow
    # =========================================================================
    def test_failover_resilience_in_integrated_pipeline(self):
        """
        Verifica que si el proveedor primario falla (ej. timeout o error de conexión),
        FailoverLLMService conmuta transparentemente al proveedor secundario en el pipeline.
        """
        class FailingLLMService(MockLLMService):
            async def generate(self, *args, **kwargs):
                raise RuntimeError("Primary provider connection timeout (503 Service Unavailable)")

        failing_primary = FailingLLMService()
        secondary_backup = MockLLMService(canned_response="Respuesta generada por el proveedor secundario de respaldo.")
        failover_service = FailoverLLMService(primary_service=failing_primary, secondary_service=secondary_backup)

        orchestrator = get_orchestrator_service()
        orchestrator.set_llm_service(failover_service)

        resp = self.client.post(
            "/chat",
            json={"message": "Hola, ¿puedes ayudarme?"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("proveedor secundario de respaldo", data["response"])


if __name__ == "__main__":
    unittest.main()
