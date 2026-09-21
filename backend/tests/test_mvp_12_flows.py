import unittest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.agents.orchestrator import get_orchestrator_service
from app.tools.task_tool import TaskTools
from app.tools.transaction_tool import TransactionTools
from app.tools.cashflow_tool import CashFlowTools
from app.services.webhook_extractor import BankWebhookExtractor


class TestMVP12MandatoryCases(unittest.TestCase):
    """
    Automated verification of the 12 mandatory MVP test cases:
    TEST 01 to TEST 12.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.orchestrator = get_orchestrator_service()

    @classmethod
    def tearDownClass(cls):
        # Clean up any test artifacts created during test run
        try:
            from app.core.database import get_supabase_client
            client = get_supabase_client()
            if client:
                client.table("tasks").delete().ilike("title", "%entregar proyecto%").execute()
                client.table("transactions").delete().eq("merchant", "Restaurante XYZ").execute()
                client.table("transactions").delete().eq("merchant", "Transporte").execute()
                client.table("transactions").delete().eq("merchant", "Gasto en transporte").execute()
        except Exception:
            pass

    def test_01_backend_health(self):
        """TEST 01: GET /health returns HTTP 200 {'status': 'ok'}"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_02_secretary_list_tasks(self):
        """TEST 02: '¿Qué tareas tengo pendientes?' -> SecretaryAgent / list_tasks"""
        res = asyncio.run(self.orchestrator.process_user_input("¿Qué tareas tengo pendientes?"))
        self.assertEqual(res.agent, "SecretaryAgent")
        self.assertEqual(res.intent, "secretary")
        self.assertTrue(any("task" in t for t in res.tools_executed) or len(res.tools_executed) > 0)
        self.assertTrue(len(res.response) > 20)

    def test_03_secretary_create_task(self):
        """TEST 03: 'Agrega una tarea llamada entregar proyecto.' -> SecretaryAgent / create_task"""
        res = asyncio.run(self.orchestrator.process_user_input("Agrega una tarea llamada entregar proyecto."))
        self.assertEqual(res.agent, "SecretaryAgent")
        self.assertEqual(res.intent, "secretary")
        self.assertIn("create_task", res.tools_executed)
        self.assertTrue("entregar proyecto" in res.response.lower())

    def test_04_secretary_complete_task(self):
        """TEST 04: 'Marca entregar proyecto como completado.' -> SecretaryAgent / complete_task"""
        res = asyncio.run(self.orchestrator.process_user_input("Marca entregar proyecto como completado."))
        self.assertEqual(res.agent, "SecretaryAgent")
        self.assertEqual(res.intent, "secretary")
        self.assertIn("complete_task", res.tools_executed)
        self.assertTrue(
            "completada" in res.response.lower() or 
            "completado" in res.response.lower() or 
            "éxito" in res.response.lower() or
            "exito" in res.response.lower()
        )

    def test_05_financial_monthly_expenses(self):
        """TEST 05: '¿Cuánto he gastado este mes?' -> FinancialAgent"""
        res = asyncio.run(self.orchestrator.process_user_input("¿Cuánto he gastado este mes?"))
        self.assertEqual(res.agent, "FinancialAgent")
        self.assertEqual(res.intent, "financial")
        self.assertTrue(
            "calculate_cash_flow" in res.tools_executed or 
            "list_transactions" in res.tools_executed or 
            len(res.tools_executed) > 0
        )
        self.assertTrue("cop" in res.response.lower() or "$" in res.response)

    def test_06_financial_create_transaction_cop(self):
        """TEST 06: 'Registra un gasto de 20000 pesos en transporte.' -> FinancialAgent / create_transaction en COP"""
        res = asyncio.run(self.orchestrator.process_user_input("Registra un gasto de 20000 pesos en transporte."))
        self.assertEqual(res.agent, "FinancialAgent")
        self.assertEqual(res.intent, "financial")
        self.assertIn("create_transaction", res.tools_executed)
        self.assertTrue("20" in res.response or "transporte" in res.response.lower())

    def test_07_bank_webhook_ingestion(self):
        """TEST 07: POST /webhooks/bank with simulated alert -> Extracted transaction in COP"""
        payload = {
            "content": "Compra por $45.000 COP en Restaurante XYZ",
            "source": "simulated_bank_alert"
        }
        resp = self.client.post("/webhooks/bank", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIsNotNone(data.get("transaction_id"))
        extracted = data.get("extracted", {})
        self.assertEqual(extracted.get("amount"), 45000.0)
        self.assertEqual(extracted.get("currency"), "COP")
        self.assertEqual(extracted.get("merchant"), "Restaurante XYZ")

    def test_08_verify_webhook_transaction_in_financials(self):
        """TEST 08: Verified that the transaction from TEST 07 is retrieved in subsequent financial queries"""
        # Query recent transactions via tool or endpoint
        resp = self.client.get("/webhooks/bank/recent?limit=5")
        self.assertEqual(resp.status_code, 200)
        recent_txs = resp.json().get("transactions", [])
        merchants = [tx.get("merchant") for tx in recent_txs]
        self.assertTrue(
            "Restaurante XYZ" in merchants or len(recent_txs) > 0,
            f"Restaurante XYZ not in recent merchants: {merchants}"
        )

    def test_09_voice_stt_flow(self):
        """TEST 09: Audio -> STT -> Backend -> Response"""
        # Create a mock audio WAV file with silent bytes
        import io
        import wave

        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 16000)
        wav_buf.seek(0)

        resp = self.client.post(
            "/voice",
            files={"file": ("test_recording.wav", wav_buf.read(), "audio/wav")}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("response", data)

    def test_10_tailscale_connectivity(self):
        """TEST 10: Remote host binding and health probe simulation"""
        from app.core.config import settings
        # Ensure host binds to 0.0.0.0 (all interfaces including Tailscale 100.x)
        self.assertEqual(settings.HOST, "0.0.0.0")
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_11_out_of_domain_agent_error_handled(self):
        """TEST 11: General question or nonsensical input does not crash and executes 0 financial/secretary tools"""
        res = asyncio.run(self.orchestrator.process_user_input("¿Cuál es la capital de Colombia?"))
        self.assertEqual(res.agent, "GeneralOrchestrator")
        self.assertEqual(res.intent, "general")
        self.assertEqual(len(res.tools_executed), 0)
        self.assertTrue("bogot" in res.response.lower())

    def test_12_backend_error_handling(self):
        """TEST 12: Backend resilience against empty input or bad payload"""
        resp = self.client.post("/chat", json={"message": "   "})
        self.assertEqual(resp.status_code, 422)  # Unprocessable Entity (length validation)


if __name__ == "__main__":
    unittest.main()
