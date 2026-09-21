# Specification Contract: Fase 10 — Financial Agent & Independent Financial Tools

## 1. Scope & Objectives
- **Problem Statement**: Previously, `FinancialAgent` had minimal stub tools (`CashFlowTool` and `TransactionTool`) with hardcoded mock numbers, lacked credit card tracking, loan schedules, saving goal management, transaction creation/categorization, and lacked explicit anti-hallucination safeguards.
- **Objective**: Implement the complete Financial Agent (`FinancialAgent`) architecture with five independent, modular tools strictly querying and persisting to the PostgreSQL / Supabase database (with in-memory fallbacks matching `database/seeds.sql`):
  1. **`TransactionTools`** (`app/tools/transaction_tool.py`):
     - `get_transactions(limit, category, type, user_id)`: Retrieve recent banking movements and expense/income logs.
     - `create_transaction(amount, type, category, description, merchant, account_id, credit_card_id, user_id)`: Register new transactions.
     - `categorize_transaction(transaction_id, category, user_id)`: Update transaction category.
  2. **`CashFlowTools`** (`app/tools/cashflow_tool.py`):
     - `calculate_cash_flow(period, user_id)`: Compute total liquid balance, net income, total expenses, and remaining discretionary budget from actual database records.
  3. **`CreditCardTools`** (`app/tools/credit_card_tool.py`):
     - `get_credit_cards(user_id)`: Retrieve active credit cards, credit limits, current balances, available credit, cutoff days, and due dates.
  4. **`LoanTools`** (`app/tools/loan_tool.py`):
     - `get_loans(user_id)`: Retrieve active loans/mortgages, remaining balance, interest rates, monthly payments, and payment dates.
  5. **`SavingGoalTools`** (`app/tools/saving_goal_tool.py`):
     - `get_saving_goals(status, user_id)`: List saving goals, target amounts, current progress, and deadlines.
     - `update_saving_goal(goal_id, current_amount, target_amount, status, user_id)`: Modify saved amounts or targets.
- **Strict Anti-Hallucination Grounding Directive**:
  - The Financial Agent MUST NOT invent or fabricate financial figures, balances, interest rates, or card limits.
  - All numerical answers must be strictly grounded in the database records returned by the tools.
  - If a requested asset, loan, or card does not exist in the database, the agent must declare that no records exist rather than generating estimates.
- **Structured Data Return**: All tools return strictly typed `ToolResult(success, data, message)`.

---

## 2. Architecture & Contracts

### 2.1 Tool Interfaces & Methods

#### `TransactionTools` (`app/tools/transaction_tool.py`)
```python
class TransactionTools(BaseTool):
    async def get_transactions(self, limit: int = 10, category: Optional[str] = None, type: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def create_transaction(self, amount: float, type: str = "expense", category: str = "general", description: str = "", merchant: Optional[str] = None, account_id: Optional[str] = None, credit_card_id: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def categorize_transaction(self, transaction_id: str, category: str, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

#### `CashFlowTools` (`app/tools/cashflow_tool.py`)
```python
class CashFlowTools(BaseTool):
    async def calculate_cash_flow(self, period: str = "current_month", user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "calculate", **kwargs) -> ToolResult: ...
```

#### `CreditCardTools` (`app/tools/credit_card_tool.py`)
```python
class CreditCardTools(BaseTool):
    async def get_credit_cards(self, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

#### `LoanTools` (`app/tools/loan_tool.py`)
```python
class LoanTools(BaseTool):
    async def get_loans(self, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

#### `SavingGoalTools` (`app/tools/saving_goal_tool.py`)
```python
class SavingGoalTools(BaseTool):
    async def get_saving_goals(self, status: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def update_saving_goal(self, goal_id: str, current_amount: Optional[float] = None, target_amount: Optional[float] = None, status: Optional[str] = None, user_id: Optional[str] = None) -> ToolResult: ...
    async def execute(self, action: str = "list", **kwargs) -> ToolResult: ...
```

### 2.2 Backward Compatibility Aliases
- `TransactionTool = TransactionTools`
- `CashFlowTool = CashFlowTools`
- `CreditCardTool = CreditCardTools`
- `LoanTool = LoanTools`
- `SavingGoalTool = SavingGoalTools`

---

## 3. Acceptance Criteria & Scenarios (Gherkin Syntax)

### Scenario 1: Transaction Operations (Get, Create, Categorize)
- **Given** `TransactionTools` is initialized
- **When** calling `create_transaction(amount=25.50, type='expense', category='alimentos', description='Cena restaurante')`
- **Then** `ToolResult.success` is `True`, an RFC 4122 UUID is created, and the transaction is recorded
- **When** calling `get_transactions(category='alimentos')`
- **Then** the created transaction is present in the list
- **When** calling `categorize_transaction(transaction_id, category='restaurantes')`
- **Then** the transaction category is updated to `'restaurantes'`.

### Scenario 2: Cash Flow Calculation
- **Given** `CashFlowTools` is initialized
- **When** calling `calculate_cash_flow(period='current_month')`
- **Then** `ToolResult.success` is `True` and data contains `total_liquid_balance`, `monthly_income`, `monthly_expenses`, `net_cash_flow`, and `accounts` summary.

### Scenario 3: Credit Card Inquiries
- **Given** `CreditCardTools` is initialized
- **When** calling `get_credit_cards()`
- **Then** active credit cards are returned with `card_name`, `credit_limit`, `current_balance`, `available_credit`, `cutoff_day`, and `due_day`.

### Scenario 4: Loan Inquiries
- **Given** `LoanTools` is initialized
- **When** calling `get_loans()`
- **Then** active loans are returned with `lender_name`, `loan_type`, `remaining_balance`, `monthly_payment`, and `interest_rate_annual`.

### Scenario 5: Saving Goals (Get & Update)
- **Given** `SavingGoalTools` is initialized
- **When** calling `get_saving_goals()`
- **Then** saving goals are returned with `goal_name`, `target_amount`, `current_amount`, and progress percentage
- **When** calling `update_saving_goal(goal_id, current_amount=2000.00)`
- **Then** `current_amount` is updated and persisted.

### Scenario 6: Anti-Hallucination & Natural Language in FinancialAgent
- **Given** a user asks: *"¿Cuánto debo en mi tarjeta de crédito?"*
- **When** `FinancialAgent.handle()` executes
- **Then** `CreditCardTools.get_credit_cards()` is invoked, and the LLM response quotes the exact balance from the database
- **Given** a user asks about an imaginary debt: *"¿Cuánto debo de mi yate de lujo?"*
- **When** `FinancialAgent.handle()` executes
- **Then** the tools find no records, and the response explicitly states that there is no loan or debt registered for a yacht, without inventing figures.
