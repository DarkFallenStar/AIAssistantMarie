import unittest
import uuid
import asyncio
from app.core.database import get_supabase_client, DEFAULT_USER_ID
from app.tools.task_tool import TaskTools
from app.tools.transaction_tool import TransactionTools
from app.tools.cashflow_tool import CashFlowTools
from app.api.endpoints.webhooks import bank_webhook
from app.schemas.webhook import BankWebhookPayload

class TestDatabasePersistenceReal(unittest.IsolatedAsyncioTestCase):
    """
    Exhaustive database persistence tests confirming:
    - Information is written to PostgreSQL (Supabase).
    - Information survives simulated process restart (new clean tool instances).
    - DELETE operations work in database.
    - Webhook transactions persist to database and reflect in subsequent queries.
    """

    async def asyncSetUp(self):
        self.supabase = get_supabase_client()
        self.created_task_ids = []
        self.created_tx_ids = []

    async def asyncTearDown(self):
        # Clean up any test artifacts in Supabase
        if self.supabase:
            for tid in self.created_task_ids:
                try:
                    self.supabase.table("tasks").delete().eq("id", tid).execute()
                except Exception:
                    pass
            for txid in self.created_tx_ids:
                try:
                    self.supabase.table("transactions").delete().eq("id", txid).execute()
                except Exception:
                    pass

    async def test_persistence_1_task_lifecycle_and_restart(self):
        """
        TEST PERSISTENCIA 1:
        1. Crear tarea.
        2. Verificar en BD.
        3. Simular reinicio de backend creando NUEVA instancia de TaskTools sin memoria previa.
        4. Consultar tareas y verificar que la tarea persiste desde la BD.
        5. Completar tarea y verificar en BD.
        6. Eliminar tarea (DELETE) y confirmar que desaparece de la BD.
        """
        unique_title = f"Entregar proyecto final {uuid.uuid4().hex[:6]}"
        task_tools = TaskTools()

        # 1. Crear tarea
        create_res = await task_tools.create_task(
            title=unique_title,
            description="Entrega obligatoria de fin de semestre",
            priority="high",
            user_id=DEFAULT_USER_ID
        )
        self.assertTrue(create_res.success)
        task_id = create_res.data["id"]
        self.created_task_ids.append(task_id)

        # 2. Verificar existencia en Supabase
        if self.supabase:
            db_res = self.supabase.table("tasks").select("*").eq("id", task_id).execute()
            self.assertTrue(len(db_res.data) > 0, "La tarea debe existir en la tabla 'tasks' de Supabase.")
            self.assertEqual(db_res.data[0]["title"], unique_title)

        # 3. Simular REINICIO DEL BACKEND (Nueva instancia de TaskTools con memoria limpia)
        fresh_task_tools = TaskTools()
        # Ensure fresh instance has no leaked session tasks
        fresh_task_tools._tasks = [dict(t) for t in TaskTools.MOCK_TASKS]

        # 4. Consultar tareas tras el reinicio
        list_res = await fresh_task_tools.list_tasks(limit=15)
        self.assertTrue(list_res.success)
        found_task = next((t for t in list_res.data["tasks"] if t.get("id") == task_id or t.get("title") == unique_title), None)
        self.assertIsNotNone(found_task, "La tarea DEBE persistir y leerse de la BD tras reiniciar el backend.")

        # 5. Completar tarea
        complete_res = await fresh_task_tools.complete_task(task_id=task_id)
        self.assertTrue(complete_res.success)
        if self.supabase:
            db_res_updated = self.supabase.table("tasks").select("status").eq("id", task_id).execute()
            self.assertEqual(db_res_updated.data[0]["status"], "completed")

        # 6. Eliminar tarea (DELETE)
        delete_res = await fresh_task_tools.delete_task(task_id=task_id)
        self.assertTrue(delete_res.success)
        if self.supabase:
            db_res_deleted = self.supabase.table("tasks").select("*").eq("id", task_id).execute()
            self.assertEqual(len(db_res_deleted.data), 0, "La tarea DEBE haberse eliminado de la BD.")

    async def test_persistence_2_transaction_lifecycle_and_restart(self):
        """
        TEST PERSISTENCIA 2:
        1. Crear transacción en COP.
        2. Verificar en BD.
        3. Simular REINICIO DEL BACKEND (Nueva instancia de TransactionTools con _shared_transactions reiniciado).
        4. Consultar transacciones y verificar que la transacción creada en BD aparece sin ser tapada por mocks.
        5. Eliminar transacción (DELETE) y confirmar eliminación en BD.
        """
        tx_tools = TransactionTools()
        unique_desc = f"Almuerzo corporativo {uuid.uuid4().hex[:6]}"
        test_amount = 35000.0

        # 1. Crear transacción
        create_res = await tx_tools.create_transaction(
            amount=test_amount,
            type="expense",
            category="alimentacion",
            description=unique_desc,
            merchant="Restaurante Gourmet",
            currency="COP",
            user_id=DEFAULT_USER_ID
        )
        self.assertTrue(create_res.success)
        tx_id = create_res.data["id"]
        self.created_tx_ids.append(tx_id)

        # 2. Verificar en Supabase
        if self.supabase:
            db_res = self.supabase.table("transactions").select("*").eq("id", tx_id).execute()
            self.assertTrue(len(db_res.data) > 0, "La transacción debe existir en la tabla 'transactions' de Supabase.")
            self.assertEqual(float(db_res.data[0]["amount"]), test_amount)

        # 3. Simular REINICIO DEL BACKEND (Reseteo estricto del estado de memoria)
        TransactionTools.reset_mock_data()
        fresh_tx_tools = TransactionTools()

        # 4. Consultar transacciones con límite estándar (limit=10)
        list_res = await fresh_tx_tools.get_transactions(limit=10)
        self.assertTrue(list_res.success)
        found_tx = next((tx for tx in list_res.data["transactions"] if tx.get("id") == tx_id or tx.get("description") == unique_desc), None)
        self.assertIsNotNone(found_tx, "La transacción DEBE recuperarse de la BD tras el reinicio y no ser tapada por mocks.")

        # 5. Eliminar transacción (DELETE)
        delete_res = await fresh_tx_tools.delete_transaction(transaction_id=tx_id)
        self.assertTrue(delete_res.success)
        if self.supabase:
            db_res_del = self.supabase.table("transactions").select("*").eq("id", tx_id).execute()
            self.assertEqual(len(db_res_del.data), 0, "La transacción DEBE haber sido borrada de Supabase.")

    async def test_persistence_3_webhook_ingestion_and_db_query(self):
        """
        TEST PERSISTENCIA 3:
        1. Enviar notificación bancaria simulada a POST /webhooks/bank.
        2. Verificar que se guarda en PostgreSQL (Supabase).
        3. Instanciar herramienta limpia y consultar gastos con CashFlowTools.
        4. Confirmar que el gasto recién registrado se refleja en la consulta financiera.
        """
        unique_merchant = f"Crepes & Waffles {uuid.uuid4().hex[:4]}"
        webhook_content = f"Bancolombia le informa compra por $52.000 en {unique_merchant} con tarjeta terminada en 9876"

        payload = BankWebhookPayload(
            source="android_notification_listener",
            content=webhook_content,
            user_id=DEFAULT_USER_ID
        )

        response = await bank_webhook(payload, _secret_valid=True)
        self.assertEqual(response.status, "success")
        tx_id = response.transaction_id
        self.created_tx_ids.append(tx_id)

        # Verificar extracción
        self.assertEqual(response.extracted.amount, 52000.0)
        self.assertEqual(response.extracted.currency, "COP")

        # Verificar existencia física en Supabase
        if self.supabase:
            db_res = self.supabase.table("transactions").select("*").eq("id", tx_id).execute()
            self.assertTrue(len(db_res.data) > 0, "El webhook DEBE persistir la transacción en Supabase.")
            self.assertEqual(float(db_res.data[0]["amount"]), 52000.0)

        # Consultar mediante CashFlowTools para confirmar que la BD alimenta las consultas financieras
        cashflow_tool = CashFlowTools()
        cf_res = await cashflow_tool.calculate_cash_flow(period="current_month", user_id=DEFAULT_USER_ID)
        self.assertTrue(cf_res.success)
        self.assertGreater(cf_res.data["monthly_expenses"], 0.0)

if __name__ == "__main__":
    unittest.main()
