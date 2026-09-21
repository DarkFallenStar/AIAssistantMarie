# Especificación Técnica — Fase 11: Function Calling & Structured Output

## 1. Contexto y Objetivos
- **Problema**: En las Fases 8, 9 y 10, la selección de herramientas se basaba en análisis heurístico y expresiones regulares (`determine_tools`) dentro de cada agente. Además, falsos positivos por coincidencia de subcadenas (ej. `"cuenta"` dentro de `"cuéntame un chiste"`) provocaban que consultas generales y humorísticas fuesen desviadas erróneamente al agente financiero.
- **Objetivo Fase 11**:
  1. Restaurar y garantizar el correcto funcionamiento del **Intent General** para que chistes, saludos, curiosidades y consultas no operativas sean atendidas naturalmente por el asistente (`GeneralAgent`).
  2. Implementar un pipeline de **Function Calling / Structured Output** desacoplado y multi-proveedor donde el LLM genere un objeto JSON con la intención estructurada (`agent`, `tool`, `arguments`).
  3. Ejecutar la herramienta en el backend y devolver los datos estructurados al LLM para construir la respuesta final natural.

---

## 2. Contratos y Esquemas de Datos

### 2.1 Esquema de Intención Estructurada (`StructuredIntent`)
```python
class StructuredIntent(BaseModel):
    agent: Literal["financial", "secretary", "general"] = Field(..., description="Agente responsable")
    tool: Optional[str] = Field(None, description="Nombre canónico de la herramienta a invocar, o null para conversación general")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos tipados de la herramienta")
    reasoning: Optional[str] = Field(None, description="Breve explicación del razonamiento del modelo")
```

### 2.2 Catálogo Canónico de Herramientas
| Agente | Nombre de Herramienta (`tool`) | Argumentos Principales | Herramienta Backend Asociada |
|---|---|---|---|
| `financial` | `calculate_cash_flow` | `period: str` ("current_month") | `CashFlowTools.calculate` |
| `financial` | `list_transactions` | `category: Optional[str]`, `limit: int` | `TransactionTools.list` |
| `financial` | `create_transaction` | `amount: float`, `type: str`, `category: str`, `description: str`, `merchant: str` | `TransactionTools.create` |
| `financial` | `categorize_transaction` | `transaction_id: str`, `category: str` | `TransactionTools.categorize` |
| `financial` | `list_credit_cards` | (ninguno) | `CreditCardTools.list` |
| `financial` | `list_loans` | (ninguno) | `LoanTools.list` |
| `financial` | `list_saving_goals` | (ninguno) | `SavingGoalTools.list` |
| `financial` | `update_saving_goal` | `goal_id: str`, `current_amount: float` | `SavingGoalTools.update` |
| `secretary` | `list_tasks` | `status: Optional[str]`, `limit: int` | `TaskTools.list` |
| `secretary` | `create_task` | `title: str`, `due_date: Optional[str]`, `priority: str` | `TaskTools.create` |
| `secretary` | `complete_task` | `task_id: str` | `TaskTools.complete` |
| `secretary` | `list_reminders` | `timeframe: str` ("all", "today", "upcoming") | `ReminderTools.list` |
| `secretary` | `create_reminder` | `title: str`, `remind_at: str`, `channel: str` | `ReminderTools.create` |
| `secretary` | `list_emails` | `status: Optional[str]`, `limit: int` | `EmailTools.list` |
| `secretary` | `get_email` | `email_id: str` | `EmailTools.get` |
| `secretary` | `search_emails` | `search: str` | `EmailTools.search` |
| `secretary` | `draft_email` | `recipient: str`, `subject: str`, `body: str` | `EmailTools.draft` |
| `general` | `null` | (ninguno) | N/A (generación directa con `GeneralAgent`) |

---

## 3. Flujo de Ejecución (Pipeline de 2 Pasos con LLM)

```
[Usuario / Mobile App]
       │
       ▼
[OrchestratorService]
       │
       ├─► Paso 1: Llamada LLM de Intención Estructurada (Function Calling)
       │    Prompt del sistema con esquema JSON + catálogo de herramientas.
       │    Retorno: StructuredIntent(agent="...", tool="...", arguments={...})
       │
       ├─► Paso 2: Ejecución de Herramienta en Backend
       │    Si tool is None o agent == "general":
       │        Sin herramienta -> pasa directo a síntesis.
       │    Si tool existe:
       │        ToolDispatcher ejecuta la herramienta correspondiente en app.tools.
       │        Retorna ToolResult(success, data, message).
       │
       └─► Paso 3: Síntesis de Respuesta Natural
            El LLM recibe los datos estructurados devueltos por la herramienta y
            la personalidad del agente para generar la respuesta fluida al usuario.
```

---

## 4. Criterios de Aceptación (Gherkin)

### Escenario 1: Intención General (Chiste / Conversación)
- **Given**: El usuario solicita "Cuéntame un chiste" o "Hola, ¿cómo estás?".
- **When**: El orquestador procesa la solicitud mediante estructuración LLM.
- **Then**: `StructuredIntent` retorna `agent="general"` y `tool=null`.
- **And**: `GeneralAgent` produce una respuesta simpática (un chiste o saludo) sin intentar ejecutar herramientas financieras ni de secretaría.

### Escenario 2: Intención Financiera con Ejecución de Herramienta
- **Given**: El usuario consulta "¿Cuánto dinero me queda este mes?" o "¿Cuál es mi flujo de caja?".
- **When**: El orquestador invoca la extracción estructurada.
- **Then**: `StructuredIntent` retorna `agent="financial"`, `tool="calculate_cash_flow"`, `arguments={"period": "current_month"}`.
- **And**: El backend ejecuta `CashFlowTools.calculate(period="current_month")`.
- **And**: El resultado se transfiere al LLM, produciendo una respuesta ejecutiva con los datos reales.

### Escenario 3: Intención de Secretaría con Registro de Tarea/Recordatorio
- **Given**: El usuario indica "Recuérdame pagar el internet mañana a las 10am".
- **When**: El orquestador invoca la extracción estructurada.
- **Then**: `StructuredIntent` retorna `agent="secretary"`, `tool="create_reminder"`, `arguments={"title": "Pagar el internet", "remind_at": "..."}`.
- **And**: El backend ejecuta `ReminderTools.create(...)`.
- **And**: El LLM confirma amablemente la creación del recordatorio.

### Escenario 4: Tolerancia a Fallos y Fallback Resiliente
- **Given**: Si el proveedor LLM no retorna JSON válido o se produce un error de conexión transitorio.
- **When**: El analizador detecta falla de decodificación.
- **Then**: Se activa el fallback semántico con límites de palabra (`\bcuenta\b`) para garantizar que el sistema nunca arroje un HTTP 500 y degrade grácilmente.
