import sys
import asyncio
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.tools.task_tool import TaskTools
from app.tools.transaction_tool import TransactionTools
from app.tools.loan_tool import LoanTools
from app.tools.reminder_tool import ReminderTools
from app.tools.credit_card_tool import CreditCardTools
from app.agents.financial import FinancialAgent
from app.agents.secretary import SecretaryAgent
from app.agents.orchestrator import OrchestratorService
from app.core.database import get_supabase_client

async def run_verifications():
    print("=== TEST 1: TaskTools list_tasks returns strictly Supabase records ===")
    task_tool = TaskTools()
    res = await task_tool.list_tasks()
    print(f"Tasks count: {res.data['count']}")
    task_titles = [t['title'] for t in res.data['tasks']]
    print(f"Task titles: {task_titles}")
    assert res.data['count'] == 2, f"Expected 2 tasks, got {res.data['count']}"
    assert "Pagar el alquiler de la casa" not in task_titles, "Invented mock task found!"
    assert "Comprar leche y víveres" not in task_titles, "Invented mock task found!"
    print("-> PASS: Only real Supabase tasks returned.")

    print("\n=== TEST 2: LoanTools get_loans returns 0 loans (zero-mock) ===")
    loan_tool = LoanTools()
    res = await loan_tool.get_loans()
    print(f"Loans count: {res.data['count']}")
    assert res.data['count'] == 0, f"Expected 0 loans, got {res.data['count']}"
    assert res.data['total_loans_balance'] == 0, "Non-zero loan balance found!"
    print("-> PASS: Zero loans correctly reported, no $7450 mock loan.")

    print("\n=== TEST 3: ReminderTools list_reminders returns 0 reminders ===")
    rem_tool = ReminderTools()
    res = await rem_tool.list_reminders()
    print(f"Reminders count: {res.data['count']}")
    assert res.data['count'] == 0, f"Expected 0 reminders, got {res.data['count']}"
    print("-> PASS: Zero reminders correctly reported, no forced mock reminders.")

    print("\n=== TEST 4: FinancialAgent.determine_tools on '¿En qué gasté?' ===")
    fin_agent = FinancialAgent()
    tools = fin_agent.determine_tools("¿En qué gasté?")
    print(f"Tools determined for '¿En qué gasté?': {tools}")
    assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}"
    assert tools[0][0] == "transaction_tool", "Expected transaction_tool"
    assert tools[0][1].get("action") == "list", f"Expected action 'list', got {tools[0][1].get('action')}"
    print("-> PASS: '¿En qué gasté?' maps to 'list', NOT 'create'!")

    print("\n=== TEST 5: SecretaryAgent.determine_tools on '¿Cuáles son mis tareas?' ===")
    sec_agent = SecretaryAgent()
    tools = sec_agent.determine_tools("¿Cuáles son mis tareas?")
    print(f"Tools determined for '¿Cuáles son mis tareas?': {tools}")
    assert len(tools) == 1
    assert tools[0][0] == "task_tool"
    assert tools[0][1].get("action") == "list"
    print("-> PASS: '¿Cuáles son mis tareas?' maps to 'list', NOT 'create'!")

    print("\n=== TEST 6: SecretaryAgent.determine_tools on 'Dime mis recordatorios' ===")
    tools = sec_agent.determine_tools("Dime mis recordatorios")
    print(f"Tools determined for 'Dime mis recordatorios': {tools}")
    assert len(tools) == 1
    assert tools[0][0] == "reminder_tool"
    assert tools[0][1].get("action") == "list"
    print("-> PASS: 'Dime mis recordatorios' maps to 'list', NOT 'create'!")

    print("\n=== TEST 7: OrchestratorService combined query does NOT create data ===")
    client = get_supabase_client()
    initial_tasks_count = client.table("tasks").select("id", count="exact").execute().count
    initial_tx_count = client.table("transactions").select("id", count="exact").execute().count

    orchestrator = OrchestratorService()
    resp = await orchestrator.process_user_input("Dime mis tareas pendientes y cuál es mi saldo", use_llm=False)
    print(f"Orchestrator response intent: {resp.intent}")

    decomp_query = "Dime qué tareas tengo y revisa mi saldo"
    resp2 = await orchestrator.process_user_input(decomp_query, use_llm=False)

    final_tasks_count = client.table("tasks").select("id", count="exact").execute().count
    final_tx_count = client.table("transactions").select("id", count="exact").execute().count

    print(f"Tasks before: {initial_tasks_count}, Tasks after: {final_tasks_count}")
    print(f"Transactions before: {initial_tx_count}, Transactions after: {final_tx_count}")
    assert final_tasks_count == initial_tasks_count, f"Task count changed! {initial_tasks_count} -> {final_tasks_count}"
    assert final_tx_count == initial_tx_count, f"Transaction count changed! {initial_tx_count} -> {final_tx_count}"
    print("-> PASS: Querying tasks and cash flow did NOT create any task or transaction in Supabase!")

    print("\n==========================================")
    print("ALL 7 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_verifications())
