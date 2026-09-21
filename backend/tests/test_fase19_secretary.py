import unittest
import asyncio
from app.tools.email_tool import EmailTools
from app.tools.task_tool import TaskTools
from app.agents.secretary import SecretaryAgent
from app.services.llm.mock import MockLLMService

class TestFase19Secretary(unittest.TestCase):
    def setUp(self):
        self.email_tools = EmailTools()
        self.task_tools = TaskTools()
        self.mock_llm = MockLLMService(canned_response="Acción de secretaría procesada.")
        self.agent = SecretaryAgent(llm_service=self.mock_llm)

    # -------------------------------------------------------------
    # 1. Listar Correos
    # -------------------------------------------------------------
    def test_listar_correos_all(self):
        res = asyncio.run(self.email_tools.list_emails())
        self.assertTrue(res.success)
        self.assertIn("emails", res.data)
        self.assertGreaterEqual(res.data["count"], 1)
        for email in res.data["emails"]:
            self.assertIn("id", email)
            self.assertIn("sender", email)
            self.assertIn("subject", email)

    def test_listar_correos_no_leidos(self):
        res = asyncio.run(self.email_tools.list_unread_emails(limit=5))
        self.assertTrue(res.success)
        self.assertIn("emails", res.data)
        # All returned emails must be unread or draft
        for email in res.data["emails"]:
            self.assertIn(email.get("status"), ["unread", "draft"])

    # -------------------------------------------------------------
    # 2. Buscar Correo
    # -------------------------------------------------------------
    def test_buscar_correo_con_coincidencia(self):
        res = asyncio.run(self.email_tools.search_emails("decano"))
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.data["count"], 1)
        first_email = res.data["emails"][0]
        self.assertTrue(
            "decano" in first_email["sender"].lower() or 
            "decano" in first_email["subject"].lower() or 
            "decano" in first_email["body"].lower()
        )

    def test_buscar_correo_sin_coincidencia(self):
        res = asyncio.run(self.email_tools.search_emails("termino_imposible_xyz_999"))
        self.assertTrue(res.success)
        self.assertEqual(res.data["count"], 0)
        self.assertEqual(res.data["emails"], [])

    def test_obtener_correo_por_id(self):
        list_res = asyncio.run(self.email_tools.list_emails())
        first_id = list_res.data["emails"][0]["id"]

        get_res = asyncio.run(self.email_tools.get_email(first_id))
        self.assertTrue(get_res.success)
        self.assertEqual(get_res.data["id"], first_id)

    # -------------------------------------------------------------
    # 3. Crear Tarea
    # -------------------------------------------------------------
    def test_crear_tarea(self):
        res = asyncio.run(self.task_tools.create_task(
            title="Preparar reporte semestral de operaciones",
            description="Revisar balances y KPIs",
            due_date="2026-10-15",
            priority="high"
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["title"], "Preparar reporte semestral de operaciones")
        self.assertEqual(res.data["priority"], "high")
        self.assertEqual(res.data["status"], "pending")
        self.assertTrue(bool(res.data["id"]))

    def test_crear_tarea_via_agent_nl(self):
        resp = asyncio.run(self.agent.handle("Crea una tarea urgente para entregar informe final"))
        self.assertEqual(resp.agent_name, "SecretaryAgent")
        self.assertIn("task_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertEqual(resp.tool_results[0].data["status"], "pending")

    # -------------------------------------------------------------
    # 4. Completar Tarea
    # -------------------------------------------------------------
    def test_completar_tarea_existente(self):
        # Create a fresh task first
        create_res = asyncio.run(self.task_tools.create_task(
            title="Tarea para completar en Fase 19",
            priority="medium"
        ))
        task_id = create_res.data["id"]

        # Complete it
        comp_res = asyncio.run(self.task_tools.complete_task(task_id=task_id))
        self.assertTrue(comp_res.success)
        self.assertEqual(comp_res.data["status"], "completed")
        self.assertIsNotNone(comp_res.data.get("completed_at"))
        asyncio.run(self.task_tools.delete_task(task_id))

    def test_completar_tarea_inexistente(self):
        comp_res = asyncio.run(self.task_tools.complete_task(task_id="00000000-0000-0000-0000-000000000000"))
        # Should gracefully fail or indicate not found without crashing
        self.assertFalse(comp_res.success)

if __name__ == "__main__":
    unittest.main()
