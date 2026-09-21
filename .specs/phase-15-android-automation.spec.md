# Specification: Phase 15 — Android Bank Notification Automation

## 1. Scope & Objectives
Implement the complete Android notification ingestion pipeline for bank transaction alerts.

### Problem Definition
Bank notifications arrive natively on Android via push notifications (e.g., Bancolombia, Nequi, Nu, Davivienda) or SMS. The system must capture these notifications, route them across the secure network link (Tailscale / LAN) to the FastAPI backend webhook (`POST /webhooks/bank`), extract structured transaction data using LLM Structured Output, and persist the records into PostgreSQL.

### Architecture & Practical Feasibility Analysis
1. **Expo Go vs Native Android**:
   - Expo Go is a pre-compiled client that does not include native `NotificationListenerService` bindings or `BIND_NOTIFICATION_LISTENER_SERVICE` permissions.
   - For workshop evaluation, we provide a dual-demonstration approach:
     - **Path A (Zero-Friction Live Demo / Expo Go)**: Automated Android Macro via **MacroDroid** (uses native Android `NotificationListenerService` to intercept real bank/SMS notifications and trigger HTTP POST to the backend) combined with an **In-App Bank Notification Automation & Simulation Center** in React Native.
     - **Path B (Native Reference / Production)**: Complete native Kotlin `NotificationListenerService` implementation (`BankNotificationListenerService.kt`) with `AndroidManifest.xml` declaration and React Native headless task bridge for custom builds.

---

## 2. End-to-End Flow

```
[ BANCO / SMS ]
       │
       ▼ (Push Notification)
[ ANDROID OS NOTIFICATION CENTER ]
       │
       ▼ (android.service.notification.NotificationListenerService)
[ NotificationListenerService / MacroDroid Trigger ]
       │
       ▼ (HTTP POST payload: {"source": "bank", "content": "..."})
[ TAILSCALE / LAN SECURE TUNNEL ]
       │
       ▼
[ BACKEND: POST /webhooks/bank ]
       │
       ▼
[ LLM STRUCTURED OUTPUT (Gemini / Ollama) ]
       │
       ▼
[ SUPABASE / POSTGRESQL (transactions) ]
```

---

## 3. Contracts & Schemas

### A. Webhook Ingestion Contract (`POST /webhooks/bank`)
- **Headers**:
  - `Content-Type: application/json`
  - `X-Webhook-Secret: [optional]`
- **Body**:
  ```json
  {
    "source": "bank_notification",
    "content": "Compra por $45.000 en Supermercado Metro con tarjeta credito",
    "user_id": "a0000000-0000-0000-0000-000000000001"
  }
  ```

### B. Recent Webhook Transactions Endpoint (`GET /webhooks/bank/recent`)
To allow the mobile app to monitor ingested transactions in real time:
- **Response**:
  ```json
  {
    "status": "success",
    "total": 5,
    "transactions": [
      {
        "id": "uuid",
        "amount": 45000.0,
        "currency": "COP",
        "merchant": "Supermercado Metro",
        "category": "food",
        "type": "expense",
        "source": "webhook_bank",
        "created_at": "2026-09-21T12:00:00Z"
      }
    ]
  }
  ```

---

## 4. Acceptance Criteria & Scenarios (Gherkin)

### Scenario 1: Interception & Webhook Dispatch
- **Given** an Android push notification received with bank transaction content
- **When** the listener service extracts the text and dispatches an HTTP POST to `/webhooks/bank`
- **Then** the backend returns HTTP 200 with `status="success"` and the parsed transaction details.

### Scenario 2: In-App Simulation & Real-time Verification
- **Given** the user navigates to the "Automatización Bancaria" screen in the React Native app
- **When** the user selects a bank preset (e.g. Bancolombia, Nequi, Nu) or enters custom notification text and taps "Enviar Notificación Simulada"
- **Then** the app sends the webhook, displays the LLM extraction results (monto, comercio, método de pago, categoría), and adds the transaction to the live monitor list.

### Scenario 3: Real Android Notification with MacroDroid / Automate
- **Given** an Android phone running MacroDroid with the provided bank notification listener macro
- **When** a real notification containing "Compra por $..." or "Transferencia recibida por $..." arrives
- **Then** MacroDroid executes the HTTP POST request to the backend Tailscale IP automatically in background.

---

## 5. Impacted Components
- `mobile/src/screens/NotificationAutomationScreen.tsx` [NEW]: Pantalla de control, monitoreo en tiempo real, simulación de notificaciones y guía de configuración Android.
- `src/screens/NotificationAutomationScreen.tsx` [NEW]: Sincronización en raíz para Expo.
- `mobile/src/services/api.ts` & `src/services/api.ts` [MODIFY]: Funciones `sendBankWebhook` y `getRecentWebhookTransactions`.
- `mobile/App.tsx` & `App.tsx` [MODIFY]: Navegación entre Asistente, Diagnóstico y Automatización Bancaria.
- `backend/app/api/endpoints/webhooks.py` [MODIFY]: Endpoint `GET /webhooks/bank/recent` para consulta en vivo de transacciones capturadas.
- `docs/android_notification_listener.md` [NEW]: Documentación técnica de `NotificationListenerService` nativo (Kotlin + AndroidManifest.xml) y receta de MacroDroid.
- `backend/tests/test_bank_webhook.py` [MODIFY]: Pruebas de integración para consulta de transacciones recientes.
