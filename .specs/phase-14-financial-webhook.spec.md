# Specification: Phase 14 — Financial Webhook Ingestion (`POST /webhooks/bank`)

## 1. Scope & Objectives
Implement the financial bank webhook endpoint to automatically ingest, extract, categorize, and persist incoming bank notification events into PostgreSQL / Supabase `transactions`.

### Problem & Motivation
Financial transactions frequently arrive via external notification channels (e.g. SMS forwarding, bank push webhook callbacks, third-party aggregators). The assistant must receive these events, parse arbitrary unstructured bank alert text into structured financial models using LLM Structured Output (with deterministic heuristic fallback), and record the transaction in the database under `source: 'webhook_bank'`.

### User-Specified Flow
1. Receive event at `POST /webhooks/bank`:
   ```json
   {
       "source": "bank",
       "content": "Compra realizada por $45.000 en ..."
   }
   ```
2. Validate webhook payload (source presence, non-empty content, optional header/token).
3. Extract information utilizing **Structured Output**.
4. Obtain:
   - `amount` (float, e.g., 45000)
   - `currency` (string, e.g., "COP")
   - `merchant` (string, e.g., "Comercio X")
   - `date` (ISO string, e.g., "2026-09-21T12:00:00Z")
   - `payment_method` (string, e.g., "credit_card")
   - `category` (string, e.g., "food")
5. Create and persist transaction in PostgreSQL (`transactions` table).

---

## 2. Contracts & Schemas

### Request Schema (`BankWebhookPayload`)
```python
class BankWebhookPayload(BaseModel):
    source: str = Field(..., example="bank", description="Origen de la notificación bancaria")
    content: str = Field(..., example="Compra realizada por $45.000 en Restaurante X con TC", description="Texto de la notificación")
    user_id: Optional[str] = Field(default=None, description="UUID del usuario receptor (por defecto DEFAULT_USER_ID)")
```

### Extracted Model (`ExtractedBankTransaction`)
```python
class ExtractedBankTransaction(BaseModel):
    amount: float = Field(..., example=45000.0, description="Monto de la transacción")
    currency: str = Field(default="COP", example="COP", description="Moneda (COP, USD, EUR, etc.)")
    merchant: str = Field(..., example="Comercio X", description="Nombre del comercio o beneficiario")
    date: str = Field(..., example="2026-09-21T12:00:00Z", description="Fecha de la transacción")
    payment_method: str = Field(default="credit_card", example="credit_card", description="Medio de pago (credit_card, debit_card, transfer)")
    category: str = Field(default="general", example="food", description="Categoría asignada")
    type: str = Field(default="expense", example="expense", description="Tipo (expense | income)")
```

### Response Schema (`BankWebhookResponse`)
```python
class BankWebhookResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(..., description="Descripción del resultado")
    transaction_id: str = Field(..., description="UUID asignado a la transacción")
    extracted: ExtractedBankTransaction
```

---

## 3. Database Mapping (PostgreSQL / Supabase `transactions`)
- `id`: `UUID` (`str(uuid.uuid4())`)
- `user_id`: `UUID` (validated UUID or `DEFAULT_USER_ID`)
- `type`: `extracted.type` (`'expense'` or `'income'`, conforms to `CHECK (type IN ('income', 'expense', 'transfer'))`)
- `amount`: `extracted.amount`
- `currency`: `extracted.currency`
- `category`: `extracted.category`
- `description`: `f"Compra en {merchant} vía {payment_method}"`
- `merchant`: `extracted.merchant`
- `transaction_date`: `extracted.date`
- `status`: `'posted'`
- `source`: `'webhook_bank'` (conforms to `CHECK (source IN ('manual', 'webhook_bank', 'voice_agent', 'email_import'))`)
- `metadata`: `{"payment_method": extracted.payment_method, "raw_content": payload.content, "source": payload.source}`

---

## 4. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Valid Bank Purchase Notification
- **Given** a POST request to `/webhooks/bank` with payload:
  `{"source": "bank", "content": "Compra por $45.000 en Supermercado Metro con tarjeta credito"}`
- **When** the backend validates the payload and invokes the structured extraction
- **Then** `amount` is 45000, `currency` is "COP", `merchant` contains "Supermercado Metro", `payment_method` is "credit_card", and `category` is "food" or "supermercado"
- **And** the transaction is inserted into PostgreSQL with `source="webhook_bank"`
- **And** response status is 200 with `status="success"`.

### Scenario 2: Transfer / Income Notification
- **Given** a POST request with payload:
  `{"source": "bank", "content": "Transferencia recibida por $120.000 de Juan Perez"}`
- **When** processed by the webhook
- **Then** `amount` is 120000, `type` is "income", and transaction is persisted successfully.

### Scenario 3: Missing or Invalid Payload
- **Given** a POST request with empty content or missing source
- **When** sent to `/webhooks/bank`
- **Then** the endpoint rejects with HTTP 400.

### Scenario 4: LLM Degradation / Offline Resilience
- **Given** LLM service is disconnected or times out
- **When** a bank notification is received
- **Then** heuristic regex extractor parses amount, currency, and merchant without failing the request.

---

## 5. Impacted Components
- `backend/app/schemas/webhook.py` [NEW]
- `backend/app/services/webhook_extractor.py` [NEW]
- `backend/app/tools/transaction_tool.py` [MODIFY]
- `backend/app/api/endpoints/webhooks.py` [NEW]
- `backend/app/main.py` [MODIFY]
- `backend/tests/test_bank_webhook.py` [NEW]
