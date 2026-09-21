import unittest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from starlette.testclient import TestClient
from app.main import app
from app.schemas.llm import LLMRole, LLMMessage, LLMResponse
from app.services.llm.base import (
    BaseLLMService,
    LLMServiceError,
    LLMConnectionError,
    LLMConfigurationError,
)
from app.services.llm.mock import MockLLMService
from app.services.llm.ollama import OllamaService
from app.services.llm.google import GoogleAIService
from app.services.llm import get_llm_service, set_llm_service
from app.agents.orchestrator import OrchestratorService

class TestLLMServiceLayer(unittest.TestCase):
    def tearDown(self):
        set_llm_service(None)

    # -------------------------------------------------------------
    # 1. MockLLMService Tests
    # -------------------------------------------------------------
    def test_mock_service_generate_and_chat(self):
        mock_svc = MockLLMService()
        self.assertEqual(mock_svc.provider_name, "mock")
        self.assertEqual(mock_svc.model_name, "mock-model")

        # Test generate
        resp = asyncio.run(mock_svc.generate("Hola asistente", system_prompt="Eres un bot"))
        self.assertIsInstance(resp, LLMResponse)
        self.assertEqual(resp.provider, "mock")
        self.assertIn("Hola asistente", resp.text)

        # Test custom canned response
        mock_svc.set_canned_response("Respuesta personalizada mock")
        resp2 = asyncio.run(mock_svc.chat([
            LLMMessage(role=LLMRole.USER, content="Pregunta 2")
        ]))
        self.assertEqual(resp2.text, "Respuesta personalizada mock")
        self.assertEqual(len(mock_svc.history), 2)

    # -------------------------------------------------------------
    # 2. Factory and Provider Resolution Tests
    # -------------------------------------------------------------
    def test_factory_resolves_providers_without_modifying_agents(self):
        # Override with mock
        set_llm_service(None)
        svc_mock = get_llm_service(provider="mock")
        self.assertIsInstance(svc_mock, MockLLMService)

        svc_ollama = get_llm_service(provider="ollama")
        self.assertIsInstance(svc_ollama, OllamaService)
        self.assertEqual(svc_ollama.provider_name, "ollama")

        svc_google = get_llm_service(provider="google")
        self.assertIsInstance(svc_google, GoogleAIService)
        self.assertEqual(svc_google.provider_name, "google")

        # Fallback on unknown
        svc_fallback = get_llm_service(provider="unknown_provider")
        self.assertIsInstance(svc_fallback, MockLLMService)

    def test_factory_set_override(self):
        custom_mock = MockLLMService(canned_response="Canned Factory Response")
        set_llm_service(custom_mock)
        active = get_llm_service()
        self.assertIs(active, custom_mock)

    # -------------------------------------------------------------
    # 3. OllamaService Tests
    # -------------------------------------------------------------
    @patch("httpx.AsyncClient.post")
    def test_ollama_service_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "llama3.2",
            "message": {
                "role": "assistant",
                "content": "Respuesta desde Ollama"
            },
            "done": True
        }
        mock_post.return_value = mock_resp

        ollama = OllamaService(base_url="http://localhost:11434", model="llama3.2")
        messages = [
            LLMMessage(role=LLMRole.USER, content="Cuanto dinero me queda?")
        ]
        result = asyncio.run(ollama.chat(messages, system_prompt="Eres financiero"))

        self.assertEqual(result.provider, "ollama")
        self.assertEqual(result.model, "llama3.2")
        self.assertEqual(result.text, "Respuesta desde Ollama")

        # Verify call payload
        call_args = mock_post.call_args
        self.assertIn("/api/chat", call_args[0][0])
        payload = call_args[1]["json"]
        self.assertEqual(payload["model"], "llama3.2")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["role"], "user")

    @patch("httpx.AsyncClient.post")
    def test_ollama_service_connection_failure(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        ollama = OllamaService(base_url="http://127.0.0.1:9999")

        with self.assertRaises(LLMConnectionError):
            asyncio.run(ollama.generate("Hola"))

    @patch("httpx.AsyncClient.post")
    def test_ollama_service_http_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        ollama = OllamaService()
        with self.assertRaises(LLMServiceError):
            asyncio.run(ollama.generate("Hola"))

    # -------------------------------------------------------------
    # 4. GoogleAIService Tests
    # -------------------------------------------------------------
    def test_google_service_missing_api_key(self):
        google_svc = GoogleAIService(api_key="")
        with self.assertRaises(LLMConfigurationError):
            asyncio.run(google_svc.generate("Hola"))

    @patch("httpx.AsyncClient.post")
    def test_google_service_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Respuesta desde Gemini 2.0 Flash"}],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ]
        }
        mock_post.return_value = mock_resp

        google_svc = GoogleAIService(api_key="test_api_key", model="gemini-2.0-flash")
        messages = [
            LLMMessage(role=LLMRole.USER, content="Como va mi presupuesto?")
        ]
        result = asyncio.run(google_svc.chat(messages, system_prompt="Eres financiero"))

        self.assertEqual(result.provider, "google")
        self.assertEqual(result.model, "gemini-2.0-flash")
        self.assertEqual(result.text, "Respuesta desde Gemini 2.0 Flash")

        # Verify Google format mapping
        call_args = mock_post.call_args
        self.assertIn("gemini-2.0-flash:generateContent", call_args[0][0])
        payload = call_args[1]["json"]
        self.assertIn("systemInstruction", payload)
        self.assertEqual(payload["contents"][0]["role"], "user")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "Como va mi presupuesto?")

    @patch("httpx.AsyncClient.post")
    def test_google_service_connection_error(self, mock_post):
        mock_post.side_effect = httpx.ConnectError("Network unreachable")
        google_svc = GoogleAIService(api_key="test_api_key")

        with self.assertRaises(LLMConnectionError):
            asyncio.run(google_svc.generate("Hola"))

    # -------------------------------------------------------------
    # 5. Orchestrator Integration Tests
    # -------------------------------------------------------------
    def test_orchestrator_delegates_to_llm_service(self):
        mock_llm = MockLLMService(canned_response="Respuesta generada por el agente financiero inteligente")
        orchestrator = OrchestratorService(llm_service=mock_llm)

        result = asyncio.run(orchestrator.process_user_input("Cuanto saldo me queda?", use_llm=True))
        self.assertEqual(result.intent, "financial")
        self.assertEqual(result.agent, "FinancialAgent")
        self.assertTrue(result.llm_used)
        self.assertEqual(result.response, "Respuesta generada por el agente financiero inteligente")

    def test_orchestrator_graceful_fallback_when_llm_fails(self):
        # Service configured with unreachable Ollama
        unreachable_ollama = OllamaService(base_url="http://127.0.0.1:9999")
        orchestrator = OrchestratorService(llm_service=unreachable_ollama)

        # Should NOT raise an unhandled exception, falls back gracefully to template
        result = asyncio.run(orchestrator.process_user_input("Cuanto saldo me queda?", use_llm=True))
        self.assertEqual(result.intent, "financial")
        self.assertFalse(result.llm_used)
        self.assertIn("consulta financiera", result.response)

    # -------------------------------------------------------------
    # 6. Chat Endpoint Integration Test
    # -------------------------------------------------------------
    def test_chat_endpoint_with_mock_llm(self):
        client = TestClient(app)
        mock_llm = MockLLMService(canned_response="Hola! Soy tu asistente impulsado por LLM.")
        set_llm_service(mock_llm)

        response = client.post("/chat", json={"message": "Hola que tal"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["response"], "Hola! Soy tu asistente impulsado por LLM.")
        self.assertEqual(data["agent"], "GeneralOrchestrator")

if __name__ == "__main__":
    unittest.main()
