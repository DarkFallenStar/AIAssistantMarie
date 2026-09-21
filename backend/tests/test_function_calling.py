import unittest
import asyncio
from app.schemas.structured import StructuredIntent
from app.tools.dispatcher import ToolDispatcher
from app.agents.orchestrator import OrchestratorService
from app.services.llm.mock import MockLLMService

class TestFunctionCalling(unittest.TestCase):

    def test_structured_intent_schema(self):
        intent = StructuredIntent(
            agent="financial",
            tool="calculate_cash_flow",
            arguments={"period": "current_month"},
            reasoning="User requested monthly cash flow"
        )
        self.assertEqual(intent.agent, "financial")
        self.assertEqual(intent.tool, "calculate_cash_flow")
        self.assertEqual(intent.arguments["period"], "current_month")

        general_intent = StructuredIntent(
            agent="general",
            tool=None,
            arguments={}
        )
        self.assertEqual(general_intent.agent, "general")
        self.assertIsNone(general_intent.tool)

    def test_tool_dispatcher_financial(self):
        async def run_async():
            dispatcher = ToolDispatcher()
            
            # 1. Cash flow tool
            res_cf = await dispatcher.dispatch("calculate_cash_flow", {"period": "current_month"})
            self.assertTrue(res_cf.success)
            self.assertIn("total_liquid_balance", res_cf.data)
            self.assertIn("net_cash_flow", res_cf.data)

            # 2. Credit cards tool
            res_cards = await dispatcher.dispatch("list_credit_cards", {})
            self.assertTrue(res_cards.success)
            self.assertIn("cards", res_cards.data)
            self.assertIsInstance(res_cards.data["cards"], list)

            # 3. Loans tool
            res_loans = await dispatcher.dispatch("list_loans", {})
            self.assertTrue(res_loans.success)
            self.assertIn("loans", res_loans.data)
            self.assertIsInstance(res_loans.data["loans"], list)

            # 4. Saving goals tool
            res_goals = await dispatcher.dispatch("list_saving_goals", {})
            self.assertTrue(res_goals.success)
            self.assertIn("goals", res_goals.data)
            self.assertIsInstance(res_goals.data["goals"], list)

        asyncio.run(run_async())

    def test_tool_dispatcher_secretary(self):
        async def run_async():
            dispatcher = ToolDispatcher()

            # 1. Create reminder
            res_rem = await dispatcher.dispatch("create_reminder", {
                "title": "Comprar medicinas",
                "remind_at": "hoy a las 4pm",
                "channel": "app"
            })
            self.assertTrue(res_rem.success)
            self.assertIn("Comprar medicinas", res_rem.message)

            # 2. Create task
            res_task = await dispatcher.dispatch("create_task", {
                "title": "Revisar informe mensual",
                "priority": "high"
            })
            self.assertTrue(res_task.success)
            self.assertIn("Revisar informe mensual", res_task.message)

            # 3. List emails
            res_emails = await dispatcher.dispatch("list_emails", {"limit": 3})
            self.assertTrue(res_emails.success)
            self.assertIn("emails", res_emails.data)
            self.assertIsInstance(res_emails.data["emails"], list)

        asyncio.run(run_async())

    def test_classify_intent_general_joke_protection(self):
        orchestrator = OrchestratorService()

        # Verifies that "cuentame un chiste" does NOT trigger financial intent despite containing "cuenta"
        joke_queries = [
            "Cuentame un chiste",
            "Dime un chiste gracioso",
            "Cuentame algo",
            "Hola Marie, como estas?",
            "Que puedes hacer?",
            "Muchas gracias por tu ayuda"
        ]
        for q in joke_queries:
            intent = orchestrator.classify_intent(q)
            self.assertEqual(intent, "general", f"Query '{q}' should be classified as 'general', got '{intent}'")

        # Verifies that financial queries still correctly route to financial
        fin_queries = [
            "Cuanto dinero me queda en mi cuenta bancaria?",
            "Cual es mi saldo disponible?",
            "Cuanto gaste en comida este mes?",
            "Cual es el limite de mi tarjeta de credito?"
        ]
        for q in fin_queries:
            intent = orchestrator.classify_intent(q)
            self.assertEqual(intent, "financial", f"Query '{q}' should be classified as 'financial', got '{intent}'")

    def test_orchestrator_general_joke_execution(self):
        async def run_async():
            mock_llm = MockLLMService(canned_response="¿Qué le dice una impresora a otra? ¿Esa hoja es tuya o es una impresión mía?")
            orchestrator = OrchestratorService(llm_service=mock_llm)

            response = await orchestrator.process_user_input("Cuentame un chiste", use_llm=True)
            self.assertEqual(response.intent, "general")
            self.assertEqual(response.agent, "GeneralOrchestrator")
            self.assertIn("impresora", response.response)
            self.assertEqual(response.tools_executed, [])

        asyncio.run(run_async())

    def test_orchestrator_function_calling_financial_flow(self):
        async def run_async():
            mock_llm = MockLLMService()
            mock_llm.set_canned_response('{"agent": "financial", "tool": "calculate_cash_flow", "arguments": {"period": "current_month"}, "reasoning": "User asks for cash flow"}')
            orchestrator = OrchestratorService(llm_service=mock_llm)

            response = await orchestrator.process_user_input("Calcula mi flujo de caja", use_llm=True)
            self.assertEqual(response.intent, "financial")
            self.assertEqual(response.agent, "FinancialAgent")
            self.assertIn("calculate_cash_flow", response.tools_executed)
            self.assertIsNotNone(response.structured_intent)
            self.assertEqual(response.structured_intent.tool, "calculate_cash_flow")

        asyncio.run(run_async())

    def test_orchestrator_function_calling_secretary_flow(self):
        async def run_async():
            mock_llm = MockLLMService()
            mock_llm.set_canned_response('{"agent": "secretary", "tool": "create_reminder", "arguments": {"title": "Llamar al médico", "remind_at": "mañana a las 10am"}, "reasoning": "User wants to create a reminder"}')
            orchestrator = OrchestratorService(llm_service=mock_llm)

            response = await orchestrator.process_user_input("Recuerdame llamar al medico manana a las 10am", use_llm=True)
            self.assertEqual(response.intent, "secretary")
            self.assertEqual(response.agent, "SecretaryAgent")
            self.assertIn("create_reminder", response.tools_executed)
            self.assertIsNotNone(response.structured_intent)
            self.assertEqual(response.structured_intent.tool, "create_reminder")

        asyncio.run(run_async())

if __name__ == "__main__":
    unittest.main()
