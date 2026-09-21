# Especificación Técnica — Fase 12: Integración Oficial de Correos & Flujo Human-in-the-Loop

## 1. Contexto y Objetivos
- **Problema**: En fases anteriores, la gestión de correos operaba de manera simulada o mediante tablas estáticas en la base de datos sin un protocolo estándar de correo (IMAP), sin capacidades avanzadas de priorización y resumen ejecutivo asistido por IA, y sin salvaguardas de confirmación humana previa al envío.
- **Objetivo Fase 12**:
  1. Diseñar e implementar una capa de abstracción de clientes de correo (`BaseEmailClient`) con soporte nativo para **IMAP local/remoto** (`IMAPEmailClient` con SSL y autenticación por contraseña de aplicación) y fallback persistente en Supabase/Mock (`MockEmailClient`).
  2. Implementar los 5 casos de uso de gestión de correos:
     - **Listar correos no leídos** (`list_unread_emails`).
     - **Buscar correos** (`search_emails`).
     - **Resumir correos** (`summarize_email` / `summarize_inbox`).
     - **Priorizar correos** (`prioritize_emails` con niveles ALTA, MEDIA, BAJA).
     - **Generar borradores** (`draft_email`).
  3. **Protocolo Obligatorio Human-in-the-Loop para Envíos**:
     Cualquier acción de envío de correos (`send_email`) DEBE requerir confirmación explícita del usuario (`requires_confirmation=True`). El correo no se enviará hasta que el usuario responda afirmativamente ("Sí, enviar", "Confirmo", "Enviar correo").

---

## 2. Contratos y Esquemas de Datos

### 2.1 Modelo de Correo (`EmailMessage`)
```python
class EmailMessage(BaseModel):
    id: str = Field(..., description="Identificador único del correo")
    sender: str = Field(..., description="Remitente (nombre y dirección)")
    recipient: str = Field(..., description="Destinatario principal")
    subject: str = Field(..., description="Asunto del correo")
    body: str = Field(..., description="Cuerpo completo en texto plano")
    snippet: str = Field(..., description="Extracto o vista previa")
    status: Literal["unread", "read", "draft", "sent"] = Field(default="unread")
    category: str = Field(default="general")
    received_at: str = Field(..., description="Fecha y hora de recepción")
    is_important: bool = Field(default=False)
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM")
```

### 2.2 Estado de Confirmación de Envío (`EmailConfirmationState`)
```python
class EmailConfirmationState(BaseModel):
    action: Literal["send_email"] = "send_email"
    recipient: str
    subject: str
    body: str
    confirmed: bool = False
    prompt: str = Field(..., description="Pregunta de confirmación generada para el usuario")
```

### 2.3 Catálogo Canónico de Herramientas de Correo
| Nombre de Herramienta | Argumentos | Descripción |
|---|---|---|
| `list_unread_emails` | `limit: int = 5` | Obtiene los correos pendientes de lectura |
| `list_emails` | `status: Optional[str]`, `limit: int = 5` | Lista correos por estado |
| `search_emails` | `query: str`, `limit: int = 5` | Búsqueda por remitente, asunto o texto |
| `summarize_email` | `email_id: str` o `query: Optional[str]` | Genera un resumen ejecutivo de puntos clave |
| `prioritize_emails` | `limit: int = 5` | Clasifica y ordena los correos por urgencia |
| `draft_email` | `recipient: str`, `subject: str`, `body: str` | Genera y guarda un borrador sin enviarlo |
| `send_email` | `recipient: str`, `subject: str`, `body: str`, `confirmed: bool` | Solicita confirmación o ejecuta el envío |

---

## 3. Arquitectura del Proveedor de Correo

```
                   ┌──────────────────────────────────────┐
                   │           SecretaryAgent             │
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
                   ┌──────────────────────────────────────┐
                   │             EmailTools               │
                   └──────────────────┬───────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
              ┌─────────────────────┐   ┌──────────────────────┐
              │   IMAPEmailClient   │   │   Supabase/Mock      │
              │  (imaplib + SSL)    │   │     EmailClient      │
              └─────────────────────┘   └──────────────────────┘
```

---

## 4. Criterios de Aceptación (Gherkin)

### Escenario 1: Listar correos no leídos
- **Given**: El usuario consulta "¿Cuáles son mis correos no leídos?" o "¿Tengo correos pendientes?".
- **When**: El orquestador extrae `tool="list_unread_emails"`.
- **Then**: El backend filtra y retorna únicamente correos con `status="unread"`.
- **And**: El agente responde indicando remitente, asunto y fecha de los correos no leídos.

### Escenario 2: Resumir correos importantes
- **Given**: El usuario solicita "Resume el correo del decano".
- **When**: El orquestador extrae `tool="summarize_email"` con argumento `query="decano"`.
- **Then**: El backend recupera el correo y el LLM produce un resumen ejecutivo conciso con puntos clave y acciones requeridas.

### Escenario 3: Priorizar correos
- **Given**: El usuario consulta "Prioriza mis correos recientes".
- **When**: El orquestador extrae `tool="prioritize_emails"`.
- **Then**: Los correos se clasifican con etiquetas ALTA (asuntos académicos/laborales clave), MEDIA y BAJA.

### Escenario 4: Confirmación previa obligatoria antes de enviar un correo
- **Given**: El usuario solicita "Envía un correo a profesor@uni.edu diciendo que ya terminé el avance".
- **When**: El agente detecta la intención de envío.
- **Then**: El sistema NO envía el correo de inmediato; en su lugar, crea un borrador y solicita confirmación explícita al usuario detallando destinatario, asunto y cuerpo.
- **And**: Únicamente cuando el usuario responda confirmando el envío ("Sí, enviar", "Confirmo"), se ejecuta el envío definitivo.
