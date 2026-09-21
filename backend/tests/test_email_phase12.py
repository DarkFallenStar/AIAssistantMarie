import unittest
import asyncio
from app.services.email import BaseEmailClient, EmailMessage, MockEmailClient, get_email_client
from app.tools.email_tool import EmailTools
from app.tools.dispatcher import ToolDispatcher
from app.agents.orchestrator import OrchestratorService
from app.services.llm.mock import MockLLMService

class TestEmailPhase12(unittest.TestCase):

    def setUp(self):
        self.mock_client = MockEmailClient()
        self.email_tools = EmailTools(email_client=self.mock_client)
        self.dispatcher = ToolDispatcher()
        self.dispatcher.email_tool = self.email_tools

    def test_list_unread_emails(self):
        async def run_async():
            res = await self.email_tools.list_unread(limit=5)
            self.assertTrue(res.success)
            self.assertIn("emails", res.data)
            self.assertGreaterEqual(res.data["count"], 1)
            for em in res.data["emails"]:
                self.assertEqual(em["status"], "unread")

        asyncio.run(run_async())

    def test_search_emails(self):
        async def run_async():
            # Search decano
            res = await self.email_tools.search_emails("decano", limit=5)
            self.assertTrue(res.success)
            self.assertGreaterEqual(res.data["count"], 1)
            first_email = res.data["emails"][0]
            self.assertIn("decano", (first_email["sender"] + first_email["subject"]).lower())

        asyncio.run(run_async())

    def test_summarize_email(self):
        async def run_async():
            # Summarize email from decano
            res = await self.email_tools.summarize_email(query="decano")
            self.assertTrue(res.success)
            self.assertIn("summary_bullet_points", res.data)
            self.assertIn("decano", res.data["sender"].lower())
            self.assertGreaterEqual(len(res.data["summary_bullet_points"]), 3)

        asyncio.run(run_async())

    def test_prioritize_emails(self):
        async def run_async():
            res = await self.email_tools.prioritize_emails(limit=5)
            self.assertTrue(res.success)
            self.assertIn("breakdown", res.data)
            self.assertIn("HIGH", res.data["breakdown"])
            self.assertGreaterEqual(res.data["count"], 2)
            # High priority should be at the top
            self.assertEqual(res.data["emails"][0]["priority"], "HIGH")

        asyncio.run(run_async())

    def test_create_email_draft(self):
        async def run_async():
            res = await self.email_tools.create_email_draft(
                recipient="rector@universidad.edu",
                subject="Informe de investigación",
                body="Estimado rector, remito el informe semestral del proyecto de IA."
            )
            self.assertTrue(res.success)
            self.assertEqual(res.data["recipient"], "rector@universidad.edu")
            self.assertEqual(res.data["status"], "draft")

        asyncio.run(run_async())

    def test_send_email_human_in_the_loop_safeguard(self):
        async def run_async():
            # 1. Without confirmation: MUST NOT send, must ask for confirmation
            res_unconfirmed = await self.email_tools.send_email_with_confirmation(
                recipient="director@uni.edu",
                subject="Entrega final",
                body="Adjunto la entrega final acordada.",
                confirmed=False
            )
            self.assertTrue(res_unconfirmed.success)
            self.assertTrue(res_unconfirmed.data["requires_confirmation"])
            self.assertIn("CONFIRMACION REQUERIDA", res_unconfirmed.message)

            # 2. With explicit confirmation: Sends successfully
            res_confirmed = await self.email_tools.send_email_with_confirmation(
                recipient="director@uni.edu",
                subject="Entrega final",
                body="Adjunto la entrega final acordada.",
                confirmed=True
            )
            self.assertTrue(res_confirmed.success)
            self.assertFalse(res_confirmed.data["requires_confirmation"])
            self.assertEqual(res_confirmed.data["status"], "sent")
            self.assertIn("enviado exitosamente", res_confirmed.message.lower())

        asyncio.run(run_async())

    def test_orchestrator_send_email_two_turn_confirmation(self):
        async def run_async():
            mock_llm = MockLLMService()
            # Turn 1: User says send email -> LLM outputs structured intent to send_email
            mock_llm.set_canned_response('{"agent": "secretary", "tool": "send_email", "arguments": {"recipient": "profesor@uni.edu", "subject": "Capitulo 3", "body": "Termine el capitulo 3", "confirmed": false}, "reasoning": "User wants to send email"}')
            orchestrator = OrchestratorService(llm_service=mock_llm)
            orchestrator.dispatcher = self.dispatcher

            # Turn 1: user asks to send
            resp1 = await orchestrator.process_user_input("Envía un correo a profesor@uni.edu con asunto Capitulo 3 diciendo Termine el capitulo 3")
            self.assertIn("CONFIRMACION REQUERIDA", resp1.response)
            self.assertIsNotNone(orchestrator._pending_confirmation)
            self.assertEqual(orchestrator._pending_confirmation["recipient"], "profesor@uni.edu")

            # Turn 2: user confirms ("Sí, enviar")
            resp2 = await orchestrator.process_user_input("Sí, confirma y envíalo por favor")
            self.assertIn("enviado exitosamente", resp2.response.lower())
            self.assertIsNone(orchestrator._pending_confirmation)

        asyncio.run(run_async())

    def test_orchestrator_send_email_cancellation(self):
        async def run_async():
            mock_llm = MockLLMService()
            mock_llm.set_canned_response('{"agent": "secretary", "tool": "send_email", "arguments": {"recipient": "amigo@gmail.com", "subject": "Cena", "body": "Vamos a cenar?", "confirmed": false}, "reasoning": "Send email"}')
            orchestrator = OrchestratorService(llm_service=mock_llm)
            orchestrator.dispatcher = self.dispatcher

            # Turn 1: trigger confirmation prompt
            await orchestrator.process_user_input("Manda un correo a amigo@gmail.com")
            self.assertIsNotNone(orchestrator._pending_confirmation)

            # Turn 2: user cancels ("No, cancela")
            resp_cancel = await orchestrator.process_user_input("No, cancela el envío")
            self.assertIn("cancelado", resp_cancel.response.lower())
            self.assertIsNone(orchestrator._pending_confirmation)

        asyncio.run(run_async())

if __name__ == "__main__":
    unittest.main()
