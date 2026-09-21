import unittest
import asyncio
from app.agents.orchestrator import OrchestratorService, get_orchestrator_service
from app.schemas.structured import StructuredIntent, SubIntentAction
from app.services.llm.mock import MockLLMService

class TestFase19Orchestrator(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MockLLMService(canned_response="Acción coordinada por el orquestador.")
        self.orchestrator = OrchestratorService(llm_service=self.mock_llm)

    def tearDown(self):
        self.orchestrator.set_llm_service(None)

    # -------------------------------------------------------------
    # 1. Identificar Secretaría
    # -------------------------------------------------------------
    def test_identificar_secretaria_heuristic(self):
        intent_task = self.orchestrator.classify_intent("Anota una tarea urgente para entregar informe")
        self.assertEqual(intent_task, "secretary")

        intent_email = self.orchestrator.classify_intent("¿Tengo algún correo nuevo del decano?")
        self.assertEqual(intent_email, "secretary")

        intent_rem = self.orchestrator.classify_intent("Recuérdame a las 4pm tomar agua")
        self.assertEqual(intent_rem, "secretary")

    def test_identificar_secretaria_structured_pipeline(self):
        # LLM returns structured secretary intent
        canned = '{"agent": "secretary", "tool": "create_task", "arguments": {"title": "Revisar examen", "priority": "high"}, "reasoning": "Crear tarea"}'
        self.orchestrator.set_llm_service(MockLLMService(canned_response=canned))

        res = asyncio.run(self.orchestrator.process_user_input("Crea una tarea para revisar el examen mañana"))
        self.assertEqual(res.intent, "secretary")
        self.assertEqual(res.agent, "SecretaryAgent")
        self.assertIn("create_task", res.tools_executed)

    # -------------------------------------------------------------
    # 2. Identificar Finanzas
    # -------------------------------------------------------------
    def test_identificar_finanzas_heuristic(self):
        intent_balance = self.orchestrator.classify_intent("¿Cuánto dinero disponible me queda en mi cuenta este mes?")
        self.assertEqual(intent_balance, "financial")

        intent_expense = self.orchestrator.classify_intent("Registra un gasto de 40 dólares en el supermercado")
        self.assertEqual(intent_expense, "financial")

        intent_cards = self.orchestrator.classify_intent("¿Cuál es el saldo de mi tarjeta de crédito?")
        self.assertEqual(intent_cards, "financial")

    def test_identificar_finanzas_structured_pipeline(self):
        # LLM returns structured financial intent
        canned = '{"agent": "financial", "tool": "calculate_cash_flow", "arguments": {"period": "current_month"}, "reasoning": "Consulta de saldo"}'
        self.orchestrator.set_llm_service(MockLLMService(canned_response=canned))

        res = asyncio.run(self.orchestrator.process_user_input("¿Cuánto dinero me queda disponible?"))
        self.assertEqual(res.intent, "financial")
        self.assertEqual(res.agent, "FinancialAgent")
        self.assertIn("calculate_cash_flow", res.tools_executed)

    # -------------------------------------------------------------
    # 3. Combinar Agentes Cuando Sea Necesario (Multi-Agent Workflow)
    # -------------------------------------------------------------
    def test_combinar_agentes_heuristic_classification(self):
        # Text containing both secretary (tarea/anota) and financial (dinero/cuenta/saldo) keywords
        compound_text = "Anota una tarea de pagar el alquiler y dime cuánto dinero me queda en la cuenta"
        intent = self.orchestrator.classify_intent(compound_text)
        self.assertEqual(intent, "combined")

    def test_combinar_agentes_structured_execution(self):
        # LLM extracts combined actions for both Secretary and Financial
        canned_combined = '''{
            "agent": "combined",
            "tool": null,
            "arguments": {},
            "actions": [
                {"agent": "secretary", "tool": "create_task", "arguments": {"title": "Pagar arriendo", "priority": "high"}},
                {"agent": "financial", "tool": "calculate_cash_flow", "arguments": {"period": "current_month"}}
            ],
            "reasoning": "Solicitud compuesta que requiere agendar tarea y consultar liquidez"
        }'''
        self.orchestrator.set_llm_service(MockLLMService(canned_response=canned_combined))

        res = asyncio.run(self.orchestrator.process_user_input("Anota una tarea para pagar el arriendo y dime cuánto saldo tengo en mis cuentas"))
        self.assertEqual(res.intent, "combined")
        self.assertEqual(res.agent, "MultiAgent")
        self.assertIn("create_task", res.tools_executed)
        self.assertIn("calculate_cash_flow", res.tools_executed)
        self.assertEqual(len(res.tools_executed), 2)
        self.assertIsNotNone(res.structured_intent)
        self.assertEqual(len(res.structured_intent.actions), 2)

    def test_combinar_agentes_heuristic_decomposition_fallback(self):
        # Simulating LLM returning non-JSON or failing structured extraction on compound input
        self.orchestrator.set_llm_service(MockLLMService(canned_response="Texto no estructurado pero válido"))

        compound_query = "Anota una tarea urgente y revisa mi saldo disponible"
        res = asyncio.run(self.orchestrator.process_user_input(compound_query))
        self.assertEqual(res.intent, "combined")
        self.assertEqual(res.agent, "MultiAgent")
        # Should have executed both secretary and financial tools via heuristic fallback
        self.assertTrue(any("task" in t for t in res.tools_executed))
        self.assertTrue(any("cash_flow" in t for t in res.tools_executed or "transactions" in t))

if __name__ == "__main__":
    unittest.main()
