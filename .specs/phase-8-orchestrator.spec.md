# Specification Contract: Fase 8 — Multi-Agent Orchestrator & Tool Execution

## 1. Scope & Objectives
- **Problem Statement**: The orchestrator currently performs basic keyword classification and queries the LLM directly without delegating to specialized agents or executing operational tools (database, email, financial cashflow).
- **Objective**: Implement a complete multi-agent Orchestrator execution pipeline:
  1. **Receive Request**: User utterance (from STT or text chat).
  2. **Analyze Intent**: Classify domain (`secretary`, `financial`, `general`).
  3. **Select Agent**: Route to `SecretaryAgent`, `FinancialAgent`, or `GeneralAgent`.
  4. **Determine Tools**: Identify necessary tools based on agent and request parameters (`EmailTool`, `TaskTool`, `CashFlowTool`, `TransactionTool`).
  5. **Execute Tools**: Query local repository or Supabase database to fetch ground truth data.
  6. **Receive Results**: Capture structured tool execution outputs.
  7. **Synthesize Final Response**: Provide the tool results and user query to the LLM (Gemini / Ollama) to craft an accurate, natural language reply.

---

## 2. Architecture & Contracts

### 2.1 Execution Flow
```
User Input ("Revisa si el decano me respondió el correo")
                      │
                      ▼
            [ORCHESTRATOR SERVICE]
                      │
                      ├─ 1. Classify Intent ("secretary")
                      ├─ 2. Route to SecretaryAgent
                      │
                      ▼
              [SECRETARY AGENT]
                      │
                      ├─ 3. Select Tool: EmailTool(query="decano")
                      ├─ 4. Execute Tool -> Database (emails table)
                      │
                      ▼
           [TOOL EXECUTION RESULT]
        {"found": true, "emails": [...]}
                      │
                      ▼
              [LLM SYNTHESIS]
(Prompt with Tool Result -> GoogleAIService / OllamaService)
                      │
                      ▼
                FINAL RESPONSE
"Sí, el decano te respondió hoy a las 10:15 am..."
```

### 2.2 Tool System (`app/tools/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class ToolResult(BaseModel):
    success: bool
    data: Any
    message: str

class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass
```

### 2.3 Concrete Tools
- **`EmailTool`** (`app/tools/email_tool.py`):
  - Action: `check_emails(sender=None, search=None, limit=5)`
  - Data Source: Supabase `emails` table (or in-memory mock repository if offline).
- **`TaskTool`** (`app/tools/task_tool.py`):
  - Actions: `create_task(title, due_date)`, `list_tasks(status)`
  - Data Source: Supabase `tasks` table.
- **`CashFlowTool`** (`app/tools/cashflow_tool.py`):
  - Action: `get_available_balance(period="current_month")`, `calculate_cashflow()`
  - Data Source: Supabase `financial_accounts`, `transactions`.
- **`TransactionTool`** (`app/tools/transaction_tool.py`):
  - Action: `get_recent_transactions(limit=5)`
  - Data Source: Supabase `transactions`.

### 2.4 Agent Architecture (`app/agents/`)
- `BaseAgent(ABC)`:
  - `name: str`
  - `system_prompt: str`
  - `tools: Dict[str, BaseTool]`
  - `async def handle(request: str, orchestrator_context: dict) -> AgentResponse`
- `SecretaryAgent`:
  - Tools: `EmailTool`, `TaskTool`
- `FinancialAgent`:
  - Tools: `CashFlowTool`, `TransactionTool`
- `GeneralAgent`:
  - General conversational assistant.

### 2.5 Orchestrator Pipeline (`app/agents/orchestrator.py`)
- `async def process_user_input(text: str, use_llm: bool = True) -> OrchestratorResponse`:
  - Step 1: Input trimming & validation.
  - Step 2: Intent classification.
  - Step 3: Agent delegation.
  - Step 4: Tool selection & execution.
  - Step 5: LLM prompt augmentation with tool context.
  - Step 6: Response generation & metadata packaging.

---

## 3. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Secretary Agent with Email Tool
- **Given** an incoming user request: *"Revisa si el decano me respondió el correo"*
- **When** the Orchestrator processes the request
- **Then** intent is classified as `secretary`
- **And** `SecretaryAgent` invokes `EmailTool` searching for *"decano"*
- **And** the tool results are provided to the LLM service
- **And** the LLM generates a personalized answer referencing the email search result.

### Scenario 2: Financial Agent with Cashflow Tool
- **Given** an incoming user request: *"¿Cuánto dinero me queda disponible este mes?"*
- **When** the Orchestrator processes the request
- **Then** intent is classified as `financial`
- **And** `FinancialAgent` invokes `CashFlowTool` to query current balance and expenses
- **And** the calculated available amount is passed to the LLM
- **And** the LLM provides an explicit summary of the user's available funds.

### Scenario 3: General Conversational Intent
- **Given** an incoming user request: *"Hola, ¿quién eres y cómo me puedes ayudar?"*
- **When** the Orchestrator processes the request
- **Then** intent is classified as `general`
- **And** no database tools are executed unnecessarily
- **And** the GeneralAgent responds warmly describing capabilities.

### Scenario 4: Offline / Database Unavailable Graceful Fallback
- **Given** database credentials are not configured or the network is unreachable
- **When** a tool execution fails
- **Then** the tool returns a `ToolResult(success=False, ...)`
- **And** the LLM informs the user politely without application crash or 500 error.

---

## 4. Impacted Components
- `backend/app/tools/base.py`: Tool interface and `ToolResult`.
- `backend/app/tools/email_tool.py`: Email search tool.
- `backend/app/tools/task_tool.py`: Task query and creation tool.
- `backend/app/tools/cashflow_tool.py`: Cash flow and balance calculation tool.
- `backend/app/tools/transaction_tool.py`: Recent transaction query tool.
- `backend/app/tools/__init__.py`: Tool registry and exports.
- `backend/app/agents/base.py`: `BaseAgent` class and contracts.
- `backend/app/agents/secretary.py`: `SecretaryAgent` implementation.
- `backend/app/agents/financial.py`: `FinancialAgent` implementation.
- `backend/app/agents/general.py`: `GeneralAgent` implementation.
- `backend/app/agents/orchestrator.py`: Multi-step orchestrator pipeline.
- `backend/tests/test_orchestrator_tools.py`: Comprehensive test suite for tools, agent routing, tool execution, and LLM synthesis.
