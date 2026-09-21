import unittest
import asyncio
from app.tools.transaction_tool import TransactionTools, TransactionTool
from app.tools.cashflow_tool import CashFlowTools, CashFlowTool
from app.tools.credit_card_tool import CreditCardTools, CreditCardTool
from app.tools.loan_tool import LoanTools, LoanTool
from app.tools.saving_goal_tool import SavingGoalTools, SavingGoalTool
from app.agents.financial import FinancialAgent
from app.services.llm.mock import MockLLMService

class TestFinancialAgentAndTools(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MockLLMService(canned_response="Consulta financiera procesada con datos exactos de la base de datos.")

    # -------------------------------------------------------------------------
    # 1. TransactionTools Tests
    # -------------------------------------------------------------------------
    def test_transaction_tools_get_transactions(self):
        tool = TransactionTools()
        res = asyncio.run(tool.get_transactions(limit=5))
        self.assertTrue(res.success)
        self.assertIn("transactions", res.data)
        self.assertGreaterEqual(res.data["count"], 1)

    def test_transaction_tools_create_transaction(self):
        tool = TransactionTools()
        res = asyncio.run(tool.create_transaction(
            amount=55.20,
            type="expense",
            category="restaurante",
            description="Almuerzo de trabajo",
            merchant="Bistro Central"
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["amount"], 55.20)
        self.assertEqual(res.data["category"], "restaurante")
        self.assertEqual(res.data["type"], "expense")

        # Verify it can be listed
        list_res = asyncio.run(tool.get_transactions(category="restaurante"))
        self.assertTrue(list_res.success)
        self.assertGreaterEqual(list_res.data["count"], 1)

    def test_transaction_tools_categorize_transaction(self):
        tool = TransactionTools()
        res = asyncio.run(tool.categorize_transaction(
            transaction_id="10000000-0000-0000-0000-000000000001",
            category="alimentos y despensa"
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["category"], "alimentos y despensa")

    def test_transaction_tools_backward_compatibility(self):
        self.assertIs(TransactionTool, TransactionTools)
        tool = TransactionTool()
        res = asyncio.run(tool.execute(action="list", limit=2))
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.data["count"], 1)

    # -------------------------------------------------------------------------
    # 2. CashFlowTools Tests
    # -------------------------------------------------------------------------
    def test_cashflow_tools_calculate(self):
        tool = CashFlowTools()
        res = asyncio.run(tool.calculate_cash_flow(period="current_month"))
        self.assertTrue(res.success)
        self.assertIn("total_liquid_balance", res.data)
        self.assertIn("monthly_income", res.data)
        self.assertIn("monthly_expenses", res.data)
        self.assertIn("net_cash_flow", res.data)
        self.assertGreater(res.data["total_liquid_balance"], 0)

    def test_cashflow_tools_backward_compatibility(self):
        self.assertIs(CashFlowTool, CashFlowTools)
        tool = CashFlowTool()
        res = asyncio.run(tool.execute())
        self.assertTrue(res.success)
        self.assertIn("total_liquid_balance", res.data)

    # -------------------------------------------------------------------------
    # 3. CreditCardTools Tests
    # -------------------------------------------------------------------------
    def test_credit_card_tools_get_cards(self):
        tool = CreditCardTools()
        res = asyncio.run(tool.get_credit_cards())
        self.assertTrue(res.success)
        self.assertIn("cards", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        card = res.data["cards"][0]
        self.assertIn("card_name", card)
        self.assertIn("credit_limit", card)
        self.assertIn("current_balance", card)
        self.assertIn("available_credit", card)
        self.assertIn("cutoff_day", card)
        self.assertIn("due_day", card)

    def test_credit_card_tools_backward_compatibility(self):
        self.assertIs(CreditCardTool, CreditCardTools)
        tool = CreditCardTool()
        res = asyncio.run(tool.execute())
        self.assertTrue(res.success)

    # -------------------------------------------------------------------------
    # 4. LoanTools Tests
    # -------------------------------------------------------------------------
    def test_loan_tools_get_loans(self):
        tool = LoanTools()
        res = asyncio.run(tool.get_loans())
        self.assertTrue(res.success)
        self.assertIn("loans", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        loan = res.data["loans"][0]
        self.assertIn("lender_name", loan)
        self.assertIn("original_amount", loan)
        self.assertIn("remaining_balance", loan)
        self.assertIn("monthly_payment", loan)
        self.assertIn("interest_rate_annual", loan)

    def test_loan_tools_backward_compatibility(self):
        self.assertIs(LoanTool, LoanTools)
        tool = LoanTool()
        res = asyncio.run(tool.execute())
        self.assertTrue(res.success)

    # -------------------------------------------------------------------------
    # 5. SavingGoalTools Tests
    # -------------------------------------------------------------------------
    def test_saving_goal_tools_get_and_update(self):
        tool = SavingGoalTools()
        res = asyncio.run(tool.get_saving_goals())
        self.assertTrue(res.success)
        self.assertIn("goals", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        goal = res.data["goals"][0]
        self.assertIn("progress_percentage", goal)

        # Update amount
        update_res = asyncio.run(tool.update_saving_goal(
            goal_id=goal["id"],
            current_amount=2500.00
        ))
        self.assertTrue(update_res.success)
        self.assertEqual(update_res.data["current_amount"], 2500.00)
        self.assertEqual(update_res.data["progress_percentage"], 50.0)

    def test_saving_goal_tools_backward_compatibility(self):
        self.assertIs(SavingGoalTool, SavingGoalTools)
        tool = SavingGoalTool()
        res = asyncio.run(tool.execute())
        self.assertTrue(res.success)

    # -------------------------------------------------------------------------
    # 6. FinancialAgent Multi-Intent NL Handling & Anti-Hallucination
    # -------------------------------------------------------------------------
    def test_financial_agent_credit_cards_intent(self):
        agent = FinancialAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("¿Cuánto debo en mi tarjeta de crédito y cuál es mi límite?"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertEqual(resp.intent, "financial")
        self.assertIn("credit_card_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertGreater(resp.tool_results[0].data["count"], 0)

    def test_financial_agent_loans_intent(self):
        agent = FinancialAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("¿Cuánto debo de mi préstamo automotriz y cuál es mi cuota mensual?"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertIn("loan_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertGreater(resp.tool_results[0].data["count"], 0)

    def test_financial_agent_saving_goal_intent(self):
        agent = FinancialAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("¿Cómo va mi meta de ahorro para el fondo de emergencia?"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertIn("saving_goal_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)

    def test_financial_agent_create_transaction_intent(self):
        agent = FinancialAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("Registra un gasto de 35 dólares en farmacia"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertIn("transaction_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertEqual(resp.tool_results[0].data["amount"], 35.0)

    def test_financial_agent_cashflow_balance_intent(self):
        agent = FinancialAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("¿Cuánto saldo disponible me queda este mes en mis cuentas?"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertIn("cashflow_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertIn("total_liquid_balance", resp.tool_results[0].data)

if __name__ == "__main__":
    unittest.main()
