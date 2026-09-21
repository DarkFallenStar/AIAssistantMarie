import unittest
import asyncio
from app.tools.email_tool import EmailTools, EmailTool
from app.tools.task_tool import TaskTools, TaskTool
from app.tools.reminder_tool import ReminderTools, ReminderTool
from app.agents.secretary import SecretaryAgent
from app.services.llm.mock import MockLLMService

class TestSecretaryAgentAndTools(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MockLLMService(canned_response="Acción de secretaría procesada correctamente.")

    # -------------------------------------------------------------------------
    # 1. EmailTools Unit Tests
    # -------------------------------------------------------------------------
    def test_email_tools_list_emails(self):
        tool = EmailTools()
        res = asyncio.run(tool.list_emails())
        self.assertTrue(res.success)
        self.assertIn("emails", res.data)
        self.assertGreaterEqual(res.data["count"], 2)

    def test_email_tools_get_email(self):
        tool = EmailTools()
        # Valid ID
        res = asyncio.run(tool.get_email("e1a1-0001"))
        self.assertTrue(res.success)
        self.assertEqual(res.data["id"], "e1a1-0001")
        self.assertIn("decano", res.data["sender"].lower())

        # Invalid ID
        bad_res = asyncio.run(tool.get_email("non-existent-id-999"))
        self.assertFalse(bad_res.success)
        self.assertIsNone(bad_res.data)

    def test_email_tools_search_emails(self):
        tool = EmailTools()
        res = asyncio.run(tool.search_emails("biblioteca"))
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.data["count"], 1)
        self.assertIn("biblioteca", res.data["emails"][0]["sender"].lower())

    def test_email_tools_create_draft(self):
        tool = EmailTools()
        res = asyncio.run(tool.create_email_draft(
            recipient="profesor@universidad.edu",
            subject="Avance de Tesis",
            body="Estimado profesor, adjunto el avance del capítulo 3 para su revisión."
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["recipient"], "profesor@universidad.edu")
        self.assertEqual(res.data["status"], "draft")
        self.assertIn("draft-", res.data["id"])

        # Check that get_email can retrieve the draft
        get_res = asyncio.run(tool.get_email(res.data["id"]))
        self.assertTrue(get_res.success)
        self.assertEqual(get_res.data["subject"], "Avance de Tesis")

    def test_email_tools_backward_compatibility_alias(self):
        self.assertIs(EmailTool, EmailTools)
        tool = EmailTool()
        res = asyncio.run(tool.execute(search="decano"))
        self.assertTrue(res.success)
        self.assertGreater(res.data["count"], 0)

    # -------------------------------------------------------------------------
    # 2. TaskTools Unit Tests
    # -------------------------------------------------------------------------
    def test_task_tools_create_and_list(self):
        tool = TaskTools()
        create_res = asyncio.run(tool.create_task(
            title="Preparar presentación para inversores",
            description="Incluir métricas de tracción y ROI",
            due_date="2026-09-30",
            priority="high"
        ))
        self.assertTrue(create_res.success)
        self.assertEqual(create_res.data["title"], "Preparar presentación para inversores")
        self.assertEqual(create_res.data["priority"], "high")
        self.assertEqual(create_res.data["status"], "pending")

        # List all
        list_res = asyncio.run(tool.list_tasks(status="pending"))
        self.assertTrue(list_res.success)
        self.assertGreaterEqual(list_res.data["count"], 3)

    def test_task_tools_update_task(self):
        tool = TaskTools()
        update_res = asyncio.run(tool.update_task(
            task_id="t1-001",
            priority="urgent",
            title="Pagar el alquiler inmediatamente"
        ))
        self.assertTrue(update_res.success)
        self.assertEqual(update_res.data["priority"], "urgent")
        self.assertEqual(update_res.data["title"], "Pagar el alquiler inmediatamente")

    def test_task_tools_complete_task(self):
        tool = TaskTools()
        comp_res = asyncio.run(tool.complete_task(task_id="t1-002"))
        self.assertTrue(comp_res.success)
        self.assertEqual(comp_res.data["status"], "completed")
        self.assertIsNotNone(comp_res.data["completed_at"])

    def test_task_tools_backward_compatibility_alias(self):
        self.assertIs(TaskTool, TaskTools)
        tool = TaskTool()
        res = asyncio.run(tool.execute(action="list"))
        self.assertTrue(res.success)
        self.assertGreater(res.data["count"], 0)

    # -------------------------------------------------------------------------
    # 3. ReminderTools Unit Tests
    # -------------------------------------------------------------------------
    def test_reminder_tools_create_and_list(self):
        tool = ReminderTools()
        res = asyncio.run(tool.create_reminder(
            title="Tomar agua y hacer estiramientos",
            remind_at="Hoy, 3:30 p.m."
        ))
        self.assertTrue(res.success)
        self.assertEqual(res.data["status"], "active")
        self.assertEqual(res.data["remind_at"], "Hoy, 3:30 p.m.")

        # List
        list_res = asyncio.run(tool.list_reminders(status="active"))
        self.assertTrue(list_res.success)
        self.assertGreaterEqual(list_res.data["count"], 3)

    def test_reminder_tools_complete(self):
        tool = ReminderTools()
        res = asyncio.run(tool.complete_reminder("rem-001"))
        self.assertTrue(res.success)
        self.assertEqual(res.data["status"], "completed")

    def test_reminder_tools_delete(self):
        tool = ReminderTools()
        del_res = asyncio.run(tool.delete_reminder("rem-002"))
        self.assertTrue(del_res.success)

        # Deleting again should return False
        del_again = asyncio.run(tool.delete_reminder("rem-002"))
        self.assertFalse(del_again.success)

    def test_reminder_tools_backward_compatibility_alias(self):
        self.assertIs(ReminderTool, ReminderTools)
        tool = ReminderTool()
        res = asyncio.run(tool.execute(action="list"))
        self.assertTrue(res.success)

    # -------------------------------------------------------------------------
    # 4. SecretaryAgent NL Multi-Intent Handling
    # -------------------------------------------------------------------------
    def test_secretary_agent_email_draft_nl(self):
        agent = SecretaryAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("Redacta un borrador de correo para director@uni.edu con asunto Convocatoria"))
        self.assertEqual(resp.agent_name, "SecretaryAgent")
        self.assertEqual(resp.intent, "secretary")
        self.assertIn("email_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertEqual(resp.tool_results[0].data["recipient"], "director@uni.edu")
        self.assertIn("Convocatoria", resp.tool_results[0].data["subject"])

    def test_secretary_agent_create_task_nl(self):
        agent = SecretaryAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("Crea una tarea urgente para entregar reporte de avance"))
        self.assertEqual(resp.agent_name, "SecretaryAgent")
        self.assertIn("task_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertEqual(resp.tool_results[0].data["priority"], "urgent")

    def test_secretary_agent_reminder_nl(self):
        agent = SecretaryAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("Recuérdame a las 5:00 pm tomar mis vitaminas"))
        self.assertEqual(resp.agent_name, "SecretaryAgent")
        self.assertIn("reminder_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertEqual(resp.tool_results[0].data["status"], "active")

    def test_secretary_agent_list_reminders_nl(self):
        agent = SecretaryAgent(llm_service=self.mock_llm)
        resp = asyncio.run(agent.handle("¿Cuáles son mis recordatorios activos?"))
        self.assertEqual(resp.agent_name, "SecretaryAgent")
        self.assertIn("reminder_tool", resp.tools_executed)
        self.assertTrue(resp.tool_results[0].success)
        self.assertGreaterEqual(resp.tool_results[0].data["count"], 1)

if __name__ == "__main__":
    unittest.main()
