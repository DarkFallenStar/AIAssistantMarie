import unittest
import io
import asyncio
from pathlib import Path
from starlette.testclient import TestClient
from app.main import app
from app.audio.stt import MockSTTService, set_stt_service
from app.services.llm import MockLLMService, set_llm_service
from app.agents.orchestrator import OrchestratorService

class TestSpeechToTextPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_text = "¿Cuánto dinero me queda disponible para salir este fin de semana?"
        self.mock_stt = MockSTTService(canned_response=self.mock_text)
        set_stt_service(self.mock_stt)
        self.mock_llm = MockLLMService(canned_response="He recibido tu consulta financiera mock.")
        set_llm_service(self.mock_llm)

    def tearDown(self):
        # Reset services to default
        set_stt_service(None)
        set_llm_service(None)

    def test_orchestrator_financial_intent(self):
        orchestrator = OrchestratorService()
        result = asyncio.run(orchestrator.process_user_input(self.mock_text, use_llm=False))
        
        self.assertEqual(result.intent, "financial")
        self.assertEqual(result.agent, "FinancialAgent")
        self.assertIn("consulta financiera", result.response)

    def test_orchestrator_secretary_intent(self):
        orchestrator = OrchestratorService()
        text = "Recuérdame comprar leche mañana en la tarde"
        result = asyncio.run(orchestrator.process_user_input(text, use_llm=False))
        
        self.assertEqual(result.intent, "secretary")
        self.assertEqual(result.agent, "SecretaryAgent")
        self.assertIn("solicitud de organizacion", result.response)

    def test_orchestrator_empty_input(self):
        orchestrator = OrchestratorService()
        result = asyncio.run(orchestrator.process_user_input("   "))
        
        self.assertEqual(result.intent, "unknown")
        self.assertIn("No logre escuchar", result.response)

    def test_voice_endpoint_stt_integration(self):
        fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....test_audio_samples")
        fake_audio.name = "test_audio.m4a"
        
        response = self.client.post(
            "/voice",
            files={"file": ("test_audio.m4a", fake_audio, "audio/m4a")}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["transcribed_text"], self.mock_text)
        self.assertEqual(data["intent"], "financial")
        self.assertIn("consulta financiera", data["response"])

    def test_voice_endpoint_empty_file_rejected(self):
        empty_audio = io.BytesIO(b"")
        response = self.client.post(
            "/voice",
            files={"file": ("empty.m4a", empty_audio, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("vacio", response.json()["detail"].lower())

if __name__ == "__main__":
    unittest.main()
