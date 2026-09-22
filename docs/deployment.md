# Guía de Despliegue y Operaciones: Puesta en Marcha en Producción y Red Privada

Este documento detalla los pasos para desplegar, configurar y operar el **Asistente Personal Inteligente Multi-Agente** tanto en entornos de desarrollo local como a través de la red mallada privada cifrada **Tailscale**.

---

## 1. Arquitectura de Despliegue

El sistema opera en una topología híbrida privada:
- **Host / Servidor**: Máquina Windows (o Linux) ejecutando el backend FastAPI en `0.0.0.0:8000`.
- **Capa LLM**: Ollama en local (`localhost:11434`) y/o Google AI Studio (API Cloud).
- **Capa de Persistencia**: PostgreSQL gestionado en Supabase Cloud.
- **Capa de Red**: Malla WireGuard privada con Tailscale (`100.x.y.z`), permitiendo que el celular se comunique con la PC desde redes 4G/5G o Wi-Fi externas sin abrir puertos en el enrutador residencial.
- **Cliente Móvil**: Dispositivo Android ejecutando la app a través de **Expo Go** o mediante binario APK autónomo (EAS Build).

---

## 2. Despliegue del Backend (FastAPI en Windows)

### Paso 1: Preparar el Entorno Virtual
1. Abre una terminal de PowerShell como Administrador o usuario estándar en la raíz del proyecto:
   ```powershell
   cd "backend"
   ```
2. Si el entorno virtual `.venv` no existe, créalo con Python 3.10+:
   ```powershell
   python -m venv .venv
   ```
3. Activa el entorno virtual:
   ```powershell
   .venv\Scripts\activate
   ```
4. Instala y actualiza las dependencias:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Paso 2: Configurar las Variables de Entorno
Copia la plantilla de entorno hacia el archivo `.env` en la raíz del proyecto:
```powershell
copy .env.example .env
```
> [!IMPORTANT]
> El archivo `.env` está estrictamente ignorado por `.gitignore` y **NUNCA** debe ser versionado en Git.

Variables esenciales en `.env`:
```env
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0

# Seguridad de Tokens (Opcional en desarrollo, Obligatorio en producción)
API_BEARER_TOKEN=tu_token_secreto_super_seguro
BANK_WEBHOOK_SECRET=tu_secreto_para_macrodroid

# Proveedor LLM: "dual" (Recomendado) | "google" | "ollama" | "mock"
LLM_PROVIDER=dual
GEMINI_API_KEY=tu_clave_de_google_ai_studio
GEMINI_MODEL=gemini-3.5-flash
GEMINI_TIMEOUT_SECONDS=25.0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Base de datos Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_service_role_o_anon_key
```

### Paso 3: Iniciar el Servidor
Ejecuta el script de inicio con recarga en caliente:
```powershell
.venv\Scripts\python.exe run.py
```
El servidor quedará a la escucha en:
- Local: `http://127.0.0.1:8000`
- LAN Wi-Fi: `http://192.168.x.x:8000`
- Tailscale VPN: `http://100.x.y.z:8000`

---

## 3. Despliegue de Base de Datos en Supabase Cloud

1. Crea un proyecto en [Supabase](https://supabase.com/).
2. Dirígete a la sección **SQL Editor** en el panel de Supabase.
3. Abre el archivo [`database/schema.sql`](file:///c:/Users/kenny/OneDrive/Documents/Cosas%20de%20movil%20que%20lo%20buguie%20todo/PersonalAssistantAI/PersonalAssistantAI/database/schema.sql), copia su contenido íntegro y ejecútalo en el SQL Editor para crear las 8 tablas, extensiones, índices y triggers.
4. Abre el archivo [`database/seeds.sql`](file:///c:/Users/kenny/OneDrive/Documents/Cosas%20de%20movil%20que%20lo%20buguie%20todo/PersonalAssistantAI/PersonalAssistantAI/database/seeds.sql), copia su contenido y ejecútalo para sembrar el usuario por defecto (`a0000000-0000-0000-0000-000000000001`), cuentas financieras de prueba, tarjetas y metas.
5. En **Project Settings -> API**, copia:
   - **Project URL** -> asignar a `SUPABASE_URL` en `.env`.
   - **service_role secret** o **anon key** -> asignar a `SUPABASE_KEY` en `.env`.
6. Verifica la conexión ejecutando `GET /db/status` en el navegador o Postman.

---

## 4. Despliegue de Red Mallada Segura con Tailscale

**Tailscale** crea un túnel WireGuard cifrado de extremo a extremo que conecta directamente la PC anfitriona y el dispositivo móvil sin exponer puertos a Internet.

### Paso 1: Configuración en la PC (Host Backend)
1. Descarga e instala el cliente oficial de Tailscale para Windows desde [tailscale.com](https://tailscale.com/).
2. Inicia sesión con tu cuenta (Google, GitHub, Microsoft).
3. Abre la consola o la bandeja del sistema y anota la dirección IP asignada a tu PC (ej: `100.95.54.56`).
4. Como FastAPI está configurado con `HOST="0.0.0.0"`, automáticamente atiende solicitudes entrantes por el adaptador virtual de Tailscale.

### Paso 2: Configuración en el Teléfono Android
1. Instala la aplicación **Tailscale** desde Google Play Store.
2. Inicia sesión con la **misma cuenta** utilizada en la PC.
3. Activa el interruptor de conexión VPN en la app de Tailscale.
4. Tu teléfono y tu PC ahora comparten la misma red privada `100.64.0.0/10`.

### Paso 3: Selector de Red de 1 Toque en la App Móvil
En la aplicación móvil, navega a la pantalla **Diagnóstico de Red**:
- Pulsa el botón **"Cambiar a Tailscale (4G / Remoto)"** para apuntar la app a `http://100.95.54.56:8000`.
- Pulsa **"Cambiar a Red Local (Wi-Fi)"** cuando ambos dispositivos estén conectados al mismo router doméstico (`http://192.168.40.15:8000`).

---

## 5. Despliegue de la Aplicación Móvil (React Native + Expo)

### Opción A: Modo Desarrollo con Expo Go (Recomendado para Pruebas e Iteración)
1. Instala las dependencias en la raíz del proyecto:
   ```powershell
   npm install
   ```
2. Asegúrate de configurar tus IPs en [`src/config/index.ts`](file:///c:/Users/kenny/OneDrive/Documents/Cosas%20de%20movil%20que%20lo%20buguie%20todo/PersonalAssistantAI/PersonalAssistantAI/src/config/index.ts):
   ```typescript
   export const DEFAULT_LAN_IP = "192.168.40.15";
   export const DEFAULT_TAILSCALE_IP = "100.95.54.56";
   export const DEFAULT_PORT = "8000";
   ```
3. Inicia el empaquetador de Expo:
   ```powershell
   npx expo start
   ```
4. Abre **Expo Go** en tu Android y escanea el código QR proyectado en la terminal.

### Opción B: Generación de APK Autónomo (Standalone) con EAS Build
Si deseas instalar el asistente como una app independiente sin depender de Expo Go:
1. Instala el CLI de Expo Application Services:
   ```powershell
   npm install -g eas-cli
   eas login
   ```
2. Configura el proyecto para compilación Android:
   ```powershell
   eas build:configure
   ```
3. Genera el instalador APK en la nube de Expo:
   ```powershell
   eas build -p android --profile preview
   ```
4. Descarga el archivo `.apk` resultante desde el enlace generado e instálalo directamente en tu dispositivo Android.

---

## 6. Despliegue de Automatización Bancaria con MacroDroid

Para capturar automáticamente compras bancarias sin requerir desarrollo nativo en Android Studio:

1. Instala **MacroDroid** desde Google Play Store en el celular del usuario.
2. Otorga el permiso de **Acceso a Notificaciones** en los ajustes del sistema de Android.
3. Crea una nueva macro:
   - **Disparador**: Notificación recibida de apps bancarias (Bancolombia, Nequi, Davivienda, Nu) con filtros de texto (`compra`, `transferencia`, `cargo`).
   - **Acción**: Solicitud HTTP `POST`.
     - URL: `http://100.95.54.56:8000/webhooks/bank`
     - Encabezados: `Content-Type: application/json` y `X-Webhook-Secret: <BANK_WEBHOOK_SECRET>`
     - Cuerpo del mensaje:
       ```json
       {
         "source": "[notification_app_name]",
         "content": "[notification_title] [notification_message]"
       }
       ```
4. Al recibir una compra, MacroDroid envía de inmediato el webhook por Tailscale al backend, el cual extrae el monto, comercio y categoría y lo persiste en PostgreSQL.

---

## 7. Mantenimiento y Solución de Problemas Operativos

### Limpieza de Procesos Huérfanos en Windows (Puerto 8000 Bloqueado)
Si al reiniciar el servidor las peticiones no llegan o aparece `[Errno 10048] Address already in use`:
```powershell
# Identificar el PID que retiene el puerto 8000
netstat -ano | findstr :8000

# Terminar el proceso fantasma de Python
Stop-Process -Id <PID> -Force
```

### Prevención de Errores de Codificación cp1252 en Consola Windows
Para evitar fallos `UnicodeEncodeError: 'charmap' codec can't encode character`:
- Los logs del backend utilizan etiquetas ASCII estandarizadas (`[VOICE]`, `[DB]`, `[API]`, `[ORCHESTRATOR]`, `[LLM]`).
- Puedes forzar UTF-8 en PowerShell ejecutando:
  ```powershell
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $env:PYTHONIOENCODING = "utf-8"
  ```
