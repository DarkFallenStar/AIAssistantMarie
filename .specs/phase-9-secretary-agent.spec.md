# Specification Contract: Fase 9 — Secretary Agent & Independent Tools

## 1. Scope & Objectives
- **Problem Statement**: The Secretary Agent previously only had basic mock implementations for simple email search and listing/creating tasks without full CRUD operations, draft handling, or dedicated reminder management.
- **Objective**: Implement the complete Secretary Agent (`SecretaryAgent`) architecture with three independent, fully structured tools:
  1. **`EmailTools`** (`app/tools/email_tool.py`):
     - `list_emails(status, limit, user_id)`: List emails with filtering by status (`unread`, `read`, etc.).
     - `get_email(email_id, user_id)`: Retrieve a single email by its unique ID.
     - `search_emails(query, limit, user_id)`: Full-text / semantic keyword search across sender, subject, and body.
     - `create_email_draft(recipient, subject, body, user_id)`: Create draft emails in the database / storage.
  2. **`TaskTools`** (`app/tools/task_tool.py`):
     - `create_task(title, description, due_date, priority, user_id)`: Create a new pending task with priority and deadline.
     - `list_tasks(status, priority, limit, user_id)`: Retrieve tasks filtered by status or priority.
     - `update_task(task_id, title, description, due_date, priority, status, user_id)`: Modify an existing task.
     - `complete_task(task_id, user_id)`: Mark a task as completed with `completed_at` timestamp.
  3. **`ReminderTools`** (`app/tools/reminder_tool.py`):
     - `create_reminder(title, remind_at, description, user_id)`: Schedule a reminder with a specific trigger date/time.
     - `list_reminders(status, limit, user_id)`: List active or past reminders.
     - `complete_reminder(reminder_id, user_id)`: Mark a reminder as dismissed/completed.
     - `delete_reminder(reminder_id, user_id)`: Delete or cancel a reminder.
- **Structured Data Return**: Every tool and method returns a strictly typed `ToolResult(success, data, message)`, where `data` is a structured dictionary or list of models.
- **Database & Offline Resilience**: Supabase database queries when connected, with full offline in-memory repository fallbacks.
- **Agent Integration**: `SecretaryAgent` delegates tasks, emails, and reminders to these independent tools, integrates context, and crafts natural conversational responses using the LLM abstraction layer.

---

## 2. Architecture & Contracts

### 2.1 Tool Interfaces & Methods

#### `EmailTools` (`app/tools/email_tool.py`)
```python
class EmailTools(BaseTool):
    async def list_emails(self, status: Optional[str] = None, limit: int = 10, user_id: Optional[str] = None) -> ToolResult: ...
    async def get_email(self, email_id: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def search_emails(self, query: str, limit: int = 10, user_id: Optional[str] = None) -> ToolResult: ...
    async def create_email_draft(self, recipient: str, subject: str, body: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

#### `TaskTools` (`app/tools/task_tool.py`)
```python
class TaskTools(BaseTool):
    async def create_task(self, title: str, description: Optional[str] = None, due_date: Optional[str] = None, priority: str = "medium", user_id: Optional[str] = None) -> ToolResult: ...
    async def list_tasks(self, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 10, user_id: Optional[str] = None) -> ToolResult: ...
    async def update_task(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[str] = None, status: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def complete_task(self, task_id: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

#### `ReminderTools` (`app/tools/reminder_tool.py`)
```python
class ReminderTools(BaseTool):
    async def create_reminder(self, title: str, remind_at: str, description: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def list_reminders(self, status: Optional[str] = "active", limit: int = 10, user_id: Optional[str] = None) -> ToolResult: ...
    async def complete_reminder(self, reminder_id: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def delete_reminder(self, reminder_id: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

### 2.2 Backward Compatibility Aliases
To guarantee zero-regression across the codebase and existing tests:
- `EmailTool = EmailTools`
- `TaskTool = TaskTools`
- `ReminderTool = ReminderTools`

### 2.3 SecretaryAgent Architecture (`app/agents/secretary.py`)
- Injects:
  - `email_tools: EmailTools`
  - `task_tools: TaskTools`
  - `reminder_tools: ReminderTools`
  - `llm_service: BaseLLMService`
- Detects natural language intent across email, task, and reminder operations:
  - Email: search query, draft creation, unread email checks, email reading.
  - Task: task creation, task listing, updating status or details, task completion.
  - Reminder: setting timed reminders, listing reminders, checking upcoming reminders.
- Synthesizes LLM responses grounded in the structured tool results.

---

## 3. Acceptance Criteria & Scenarios (Gherkin Syntax)

### Scenario 1: Email Operations (List, Get, Search, Create Draft)
- **Given** `EmailTools` is initialized
- **When** calling `search_emails(query="decano")`
- **Then** `ToolResult.success` is `True` and results contain matching emails
- **When** calling `create_email_draft(recipient="test@example.com", subject="Proyecto", body="Borrador inicial")`
- **Then** `ToolResult.success` is `True`, a valid RFC 4122 UUID is generated, and status is saved as `'draft'` (or resiliently as `'unread'` with `[Borrador]` prefix if Supabase check constraint `emails_status_check` is active)
- **When** calling `get_email(email_id=draft_id)`
- **Then** the created draft is retrieved with exact recipient, subject, and body without raising PostgreSQL `22P02`.

### Scenario 2: Task Operations (Create, List, Update, Complete)
- **Given** `TaskTools` is initialized
- **When** calling `create_task(title="Preparar reporte financiero", priority="high", due_date="2026-09-25")`
- **Then** the task is created with status `'pending'`
- **When** calling `update_task(task_id, priority="urgent", title="Preparar reporte ejecutivo")`
- **Then** the task properties are updated in storage
- **When** calling `complete_task(task_id)`
- **Then** status becomes `'completed'` and `completed_at` is set
- **When** calling `list_tasks(status="completed")`
- **Then** the task is returned in the completed list.

### Scenario 3: Reminder Operations (Create, List, Complete)
- **Given** `ReminderTools` is initialized
- **When** calling `create_reminder(title="Tomar medicina", remind_at="Hoy 8:00 PM")`
- **Then** reminder is saved with status `'active'`
- **When** calling `list_reminders(status="active")`
- **Then** the newly created reminder is listed
- **When** calling `complete_reminder(reminder_id)`
- **Then** the reminder is marked as `'completed'`.

### Scenario 4: Natural Language Handling in SecretaryAgent
- **Given** a user prompt: *"Crea una tarea para entregar el informe mañana con prioridad alta"*
- **When** `SecretaryAgent.handle()` processes the utterance
- **Then** `TaskTools.create_task` is executed with title *"entregar el informe"* and priority *"high"*
- **And** the LLM confirms the creation clearly to the user.

- **Given** a user prompt: *"Redacta un borrador de correo para profesor@uni.edu con asunto Tesis"*
- **When** `SecretaryAgent.handle()` processes the utterance
- **Then** `EmailTools.create_email_draft` is executed with recipient *"profesor@uni.edu"* and subject *"Tesis"*
- **And** the LLM confirms the draft creation.

- **Given** a user prompt: *"Recuérdame llamar al médico a las 4 de la tarde"*
- **When** `SecretaryAgent.handle()` processes the utterance
- **Then** `ReminderTools.create_reminder` is executed with reminder title and time
- **And** the LLM synthesizes a confirmation.

---

## 4. Impacted Components
- `backend/app/tools/email_tool.py`: Re-architect into `EmailTools` (`list_emails`, `get_email`, `search_emails`, `create_email_draft`, plus backwards compatibility).
- `backend/app/tools/task_tool.py`: Re-architect into `TaskTools` (`create_task`, `list_tasks`, `update_task`, `complete_task`, plus backwards compatibility).
- `backend/app/tools/reminder_tool.py`: **[NEW]** Implement `ReminderTools` (`create_reminder`, `list_reminders`, `complete_reminder`, `delete_reminder`).
- `backend/app/tools/__init__.py`: Export `EmailTools`, `EmailTool`, `TaskTools`, `TaskTool`, `ReminderTools`, `ReminderTool`.
- `backend/app/agents/secretary.py`: Integrate all three toolkits and expand parsing & synthesis for emails, tasks, and reminders.
- `backend/tests/test_secretary_agent.py`: **[NEW]** Comprehensive test suite for all methods of `EmailTools`, `TaskTools`, `ReminderTools`, and `SecretaryAgent` multi-intent handling.
