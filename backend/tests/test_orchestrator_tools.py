import unittest
import asyncio
from app.tools.email_tool import EmailTool
from app.tools.task_tool import TaskTool
from app.tools.cashflow_tool import CashFlowTool
from app.tools.transaction_tool import TransactionTool
from app.agents.secretary import SecretaryAgent
from app.agents.financial import FinancialAgent
from app.agents.general import GeneralAgent
from app.agents.orchestrator import OrchestratorService
from app.services.llm.mock import MockLLMService

class TestOrchestratorAndTools(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MockLLMService(canned_response="Sí, el decano te respondió hoy confirmando la aprobación del proyecto.")

    # -------------------------------------------------------------
    # 1. Tools Tests
    # -------------------------------------------------------------
    def test_email_tool_search_decano(self):
        tool = EmailTool()
        result = asyncio.run(tool.execute(search="decano"))
        self.assertTrue(result.success)
        self.assertGreater(result.data["count"], 0)
        first_email = result.data["emails"][0]
        self.assertIn("decano", first_email["sender"].lower())
        self.assertIn("aprobada", first_email["body"].lower())

    def test_email_tool_search_empty_result(self):
        tool = EmailTool()
        result = asyncio.run(tool.execute(search="asunto_inexistente_xyz_123"))
        self.assertTrue(result.success)
        self.assertEqual(result.data["count"], 0)

    def test_task_tool_create_and_list(self):
        tool = TaskTool()
        # Create
        create_res = asyncio.run(tool.execute(action="create", title="Revisar informe de auditoria"))
        self.assertTrue(create_res.success)
        self.assertIn("Revisar informe", create_res.message)

        # List
        list_res = asyncio.run(tool.execute(action="list"))
        self.assertTrue(list_res.success)
        self.assertGreater(list_res.data["count"], 0)

    def test_cashflow_tool_calculation(self):
        tool = CashFlowTool()
        result = asyncio.run(tool.execute(period="current_month"))
        self.assertTrue(result.success)
        self.assertIn("total_liquid_balance", result.data)
        self.assertIn("net_available_for_spending", result.data)
        self.assertGreater(result.data["total_liquid_balance"], 0)

    def test_transaction_tool_recent(self):
        tool = TransactionTool()
        result = asyncio.run(tool.execute(limit=3))
        self.assertTrue(result.success)
        self.assertLessEqual(result.data["count"], 3)

    # -------------------------------------------------------------
    # 2. Agent Execution Tests
    # -------------------------------------------------------------
    def test_secretary_agent_executes_email_tool(self):
        agent = SecretaryAgent(llm_service=self.mock_llm)
        response = asyncio.run(agent.handle("Revisa si el decano me respondió el correo."))
        
        self.assertEqual(response.agent_name, "SecretaryAgent")
        self.assertEqual(response.intent, "secretary")
        self.assertIn("email_tool", response.tools_executed)
        self.assertEqual(len(response.tool_results), 1)
        self.assertTrue(response.tool_results[0].success)
        self.assertEqual(response.final_response, "Sí, el decano te respondió hoy confirmando la aprobación del proyecto.")

    def test_financial_agent_executes_cashflow_tool(self):
        fin_mock = MockLLMService(canned_response="Tienes disponible $1,920 USD este mes para ocio y gastos.")
        agent = FinancialAgent(llm_service=fin_mock)
        response = asyncio.run(agent.handle("¿Cuánto dinero me queda disponible este mes?"))

        self.assertEqual(response.agent_name, "FinancialAgent")
        self.assertEqual(response.intent, "financial")
        self.assertIn("cashflow_tool", response.tools_executed)
        self.assertEqual(len(response.tool_results), 1)
        self.assertTrue(response.tool_results[0].success)
        self.assertIn("1,920", response.final_response)

    # -------------------------------------------------------------
    # 3. 7-Step Orchestrator Pipeline Tests
    # -------------------------------------------------------------
    def test_orchestrator_7_step_pipeline_decano_example(self):
        orchestrator = OrchestratorService(llm_service=self.mock_llm)
        result = asyncio.run(orchestrator.process_user_input("Revisa si el decano me respondió el correo."))

        self.assertEqual(result.intent, "secretary")
        self.assertEqual(result.agent, "SecretaryAgent")
        self.assertTrue(result.llm_used)
        self.assertIn("email_tool", result.tools_executed)
        self.assertIn("decano te respondió", result.response)

    def test_orchestrator_7_step_pipeline_cashflow_example(self):
        cashflow_mock = MockLLMService(canned_response="Te quedan $1,920 USD disponibles en tu balance mensual.")
        orchestrator = OrchestratorService(llm_service=cashflow_mock)
        result = asyncio.run(orchestrator.process_user_input("¿Cuánto dinero me queda disponible este mes?"))

        self.assertEqual(result.intent, "financial")
        self.assertEqual(result.agent, "FinancialAgent")
        self.assertTrue(result.llm_used)
        self.assertIn("cashflow_tool", result.tools_executed)
        self.assertIn("1,920", result.response)

    def test_orchestrator_general_intent_no_tools(self):
        gen_mock = MockLLMService(canned_response="Hola, soy tu asistente personal inteligente. ¿En qué te puedo ayudar hoy?")
        orchestrator = OrchestratorService(llm_service=gen_mock)
        result = asyncio.run(orchestrator.process_user_input("Hola, buenos días."))

        self.assertEqual(result.intent, "general")
        self.assertEqual(result.agent, "GeneralOrchestrator")
        self.assertEqual(result.tools_executed, [])

    def test_orchestrator_empty_input(self):
        orchestrator = OrchestratorService()
        result = asyncio.run(orchestrator.process_user_input("   "))
        self.assertEqual(result.intent, "unknown")
        self.assertIn("No logre escuchar", result.response)

if __name__ == "__main__":
    unittest.main()
