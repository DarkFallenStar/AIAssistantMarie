import unittest
import asyncio
from app.tools.transaction_tool import TransactionTools
from app.tools.cashflow_tool import CashFlowTools
from app.tools.saving_goal_tool import SavingGoalTools
from app.agents.financial import FinancialAgent
from app.services.llm.mock import MockLLMService

class TestFase19Financial(unittest.TestCase):
    def setUp(self):
        self.transaction_tools = TransactionTools()
        self.cashflow_tools = CashFlowTools()
        self.saving_goal_tools = SavingGoalTools()
        self.mock_llm = MockLLMService(canned_response="Consulta financiera procesada con precisión.")
        self.agent = FinancialAgent(llm_service=self.mock_llm)

    # -------------------------------------------------------------
    # 1. Registrar Transacción
    # -------------------------------------------------------------
    def test_registrar_transaccion_gasto(self):
        res = asyncio.run(self.transaction_tools.create_transaction(
            amount=75.50,
            type="expense",
            category="restaurante",
            description="Cena ejecutiva con cliente",
            merchant="Restaurante La Toscana"
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["amount"], 75.50)
        self.assertEqual(res.data["type"], "expense")
        self.assertEqual(res.data["category"], "restaurante")
        self.assertEqual(res.data["merchant"], "Restaurante La Toscana")
        self.assertTrue(bool(res.data["id"]))

    def test_registrar_transaccion_ingreso(self):
        res = asyncio.run(self.transaction_tools.create_transaction(
            amount=500.00,
            type="income",
            category="honorarios",
            description="Pago de asesoría técnica",
            merchant="Cliente Corporativo"
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["amount"], 500.00)
        self.assertEqual(res.data["type"], "income")

    # -------------------------------------------------------------
    # 2. Consultar Transacciones
    # -------------------------------------------------------------
    def test_consultar_transacciones_limit(self):
        res = asyncio.run(self.transaction_tools.get_transactions(limit=3))
        self.assertTrue(res.success)
        self.assertIn("transactions", res.data)
        self.assertLessEqual(len(res.data["transactions"]), 3)
        for tx in res.data["transactions"]:
            self.assertIn("amount", tx)
            self.assertIn("category", tx)
            self.assertIn("type", tx)

    def test_consultar_transacciones_por_categoria(self):
        # Register a transaction with a unique category to test filtering
        asyncio.run(self.transaction_tools.create_transaction(
            amount=30.00,
            type="expense",
            category="ferreteria",
            description="Compra de herramientas",
            merchant="Homecenter"
        ))
        res = asyncio.run(self.transaction_tools.get_transactions(category="ferreteria"))
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.data["count"], 1)
        for tx in res.data["transactions"]:
            self.assertEqual(tx["category"], "ferreteria")

    # -------------------------------------------------------------
    # 3. Calcular Flujo de Caja
    # -------------------------------------------------------------
    def test_calcular_flujo_de_caja(self):
        res = asyncio.run(self.cashflow_tools.calculate_cash_flow(period="current_month"))
        self.assertTrue(res.success)
        self.assertIn("total_liquid_balance", res.data)
        self.assertIn("monthly_income", res.data)
        self.assertIn("monthly_expenses", res.data)
        self.assertIn("net_cash_flow", res.data)
        self.assertGreater(res.data["total_liquid_balance"], 0)
        self.assertIsInstance(res.data["total_liquid_balance"], (int, float))

    def test_calcular_flujo_via_agent_nl(self):
        resp = asyncio.run(self.agent.handle("¿Cuánto saldo disponible me queda este mes en mis cuentas?"))
        self.assertEqual(resp.agent_name, "FinancialAgent")
        self.assertEqual(resp.intent, "financial")
        self.assertIn("cashflow_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertIn("total_liquid_balance", resp.tool_results[0].data)

    # -------------------------------------------------------------
    # 4. Consultar Metas
    # -------------------------------------------------------------
    def test_consultar_metas_de_ahorro(self):
        res = asyncio.run(self.saving_goal_tools.get_saving_goals())
        self.assertTrue(res.success)
        self.assertIn("goals", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        goal = res.data["goals"][0]
        self.assertIn("goal_name", goal)
        self.assertIn("target_amount", goal)
        self.assertIn("current_amount", goal)
        self.assertIn("progress_percentage", goal)
        self.assertGreaterEqual(goal["progress_percentage"], 0.0)

    def test_actualizar_meta_de_ahorro(self):
        list_res = asyncio.run(self.saving_goal_tools.get_saving_goals())
        goal = list_res.data["goals"][0]
        goal_id = goal["id"]

        update_res = asyncio.run(self.saving_goal_tools.update_saving_goal(
            goal_id=goal_id,
            current_amount=3000.00
        ))
        self.assertTrue(update_res.success)
        self.assertEqual(update_res.data["current_amount"], 3000.00)
        self.assertIn("progress_percentage", update_res.data)

if __name__ == "__main__":
    unittest.main()
