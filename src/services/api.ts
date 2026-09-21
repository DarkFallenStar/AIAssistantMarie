import { File, UploadType } from 'expo-file-system';
import { DEFAULT_API_TOKEN, DEFAULT_BANK_WEBHOOK_SECRET } from '../config';

export interface HealthResponse {
  status: string;
  latencyMs: number;
}

export interface ChatResponse {
  response: string;
  intent?: string;
  agent?: string;
  tools_executed?: string[];
  structured_intent?: {
    agent: string;
    tool?: string | null;
    arguments?: Record<string, any>;
    reasoning?: string;
  };
  audio_url?: string;
}

export interface DatabaseStatusResponse {
  status: string;
  connected: boolean;
  message?: string;
  supabase_url?: string;
  tables_defined?: string[];
  latencyMs?: number;
}

export interface BankWebhookPayload {
  source: string;
  content: string;
  user_id?: string;
}

export interface ExtractedBankTransaction {
  amount: number;
  currency: string;
  merchant: string;
  date: string;
  payment_method: string;
  category: string;
  type: string;
}

export interface BankWebhookResponse {
  status: string;
  message: string;
  transaction_id: string;
  extracted: ExtractedBankTransaction;
}

export interface WebhookRecentTransaction {
  id: string;
  amount: number;
  currency: string;
  merchant?: string;
  category: string;
  type: string;
  transaction_date?: string;
  metadata?: Record<string, any>;
}

export interface WebhookRecentTransactionsResponse {
  status: string;
  total: number;
  transactions: WebhookRecentTransaction[];
}

// -----------------------------------------------------------------------------
// Authentication and Security State (Phase 17)
// -----------------------------------------------------------------------------
let _activeApiToken: string = DEFAULT_API_TOKEN;
let _activeWebhookSecret: string = DEFAULT_BANK_WEBHOOK_SECRET;

export function setApiToken(token: string) {
  _activeApiToken = (token || "").trim();
}

export function getApiToken(): string {
  return _activeApiToken;
}

export function setWebhookSecret(secret: string) {
  _activeWebhookSecret = (secret || "").trim();
}

export function getWebhookSecret(): string {
  return _activeWebhookSecret;
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = getApiToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Normalizes backend URL ensuring protocol and removing trailing slashes.
 */
export function normalizeUrl(rawUrl: string): string {
  let clean = rawUrl.trim();
  if (!clean.startsWith("http://") && !clean.startsWith("https://")) {
    clean = `http://${clean}`;
  }
  return clean.replace(/\/+$/, "");
}

/**
 * Checks connectivity with the FastAPI backend health endpoint (GET /health).
 * Measures response round-trip latency. (Public endpoint, no auth required).
 */
export async function checkBackendHealth(
  baseUrl: string,
  timeoutMs: number = 5000
): Promise<HealthResponse> {
  const url = `${normalizeUrl(baseUrl)}/health`;
  const startTime = Date.now();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const latencyMs = Date.now() - startTime;

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      status: data.status || "ok",
      latencyMs,
    };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Tiempo de espera agotado (${timeoutMs}ms). Verifica que el backend esté corriendo.`);
    }
    throw new Error(err.message || "No se pudo conectar con el backend");
  }
}

/**
 * Checks connectivity with Supabase / database endpoint (GET /db/status).
 * Measures response round-trip latency.
 */
export async function checkDatabaseStatus(
  baseUrl: string,
  timeoutMs: number = 8000
): Promise<DatabaseStatusResponse> {
  const url = `${normalizeUrl(baseUrl)}/db/status`;
  const startTime = Date.now();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders({
        Accept: "application/json",
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const latencyMs = Date.now() - startTime;

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: DatabaseStatusResponse = await response.json();
    return {
      ...data,
      latencyMs,
    };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Tiempo de espera agotado (${timeoutMs}ms) consultando estado de base de datos.`);
    }
    throw new Error(err.message || "No se pudo consultar el estado de la base de datos");
  }
}

/**
 * Sends a chat message to POST /chat and returns the response string.
 */
export async function sendChatMessage(
  baseUrl: string,
  message: string,
  timeoutMs: number = 35000
): Promise<string> {
  const url = `${normalizeUrl(baseUrl)}/chat`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders({
        "Content-Type": "application/json",
        Accept: "application/json",
      }),
      body: JSON.stringify({ message }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData?.detail) {
          errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Tiempo de espera agotado (${timeoutMs / 1000}s) esperando la respuesta del asistente. Verifica tu conexion y el estado del backend.`);
    }
    throw new Error(err.message || "Error al comunicarse con /chat");
  }
}

export interface VoiceResponse {
  status: string;
  filename: string;
  size_bytes: number;
  content_type?: string;
  transcribed_text?: string;
  intent?: string;
  message: string;
  response: string;
  audio_url?: string;
}

/**
 * Requests backend to synthesize TTS audio for given text (POST /tts?as_json=true).
 */
export async function requestTTS(
  baseUrl: string,
  text: string,
  timeoutMs: number = 10000
): Promise<{ status: string; audio_url: string; text: string }> {
  const url = `${normalizeUrl(baseUrl)}/tts?as_json=true`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders({
        "Content-Type": "application/json",
        Accept: "application/json",
      }),
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    throw new Error(err.message || "Error al sintetizar TTS en backend");
  }
}

/**
 * Sends a recorded audio file natively as multipart/form-data to POST /voice using Expo File.upload.
 */
export async function sendAudioRecording(
  baseUrl: string,
  audioUri: string
): Promise<VoiceResponse> {
  const url = `${normalizeUrl(baseUrl)}/voice`;

  try {
    const file = new File(audioUri);
    const uploadResult = await file.upload(url, {
      fieldName: 'file',
      httpMethod: 'POST',
      uploadType: UploadType.MULTIPART,
      mimeType: 'audio/m4a',
      headers: getAuthHeaders(),
    });

    if (uploadResult.status < 200 || uploadResult.status >= 300) {
      let errorDetail = `HTTP ${uploadResult.status}`;
      try {
        const parsed = JSON.parse(uploadResult.body);
        if (parsed?.detail) errorDetail = parsed.detail;
      } catch (_) {}
      throw new Error(errorDetail);
    }

    const data: VoiceResponse = JSON.parse(uploadResult.body);
    return data;
  } catch (err: any) {
    throw new Error(err.message || 'Error al subir grabación de audio a /voice');
  }
}

/**
  * Dispatches a bank notification payload to the webhook endpoint (POST /webhooks/bank).
  */
export async function sendBankWebhook(
  baseUrl: string,
  payload: BankWebhookPayload,
  webhookSecret?: string,
  timeoutMs: number = 25000
): Promise<BankWebhookResponse> {
  const url = `${normalizeUrl(baseUrl)}/webhooks/bank`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const activeSecret = (webhookSecret || getWebhookSecret() || "").trim();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (activeSecret) {
    headers['X-Webhook-Secret'] = activeSecret;
  }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData?.detail) errorDetail = errorData.detail;
      } catch (_) {}
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Tiempo de espera agotado (${timeoutMs}ms) al enviar webhook bancario.`);
    }
    throw new Error(err.message || 'Error procesando webhook bancario');
  }
}

/**
  * Fetches recent transactions captured by the bank webhook (GET /webhooks/bank/recent).
  */
export async function getRecentWebhookTransactions(
  baseUrl: string,
  limit: number = 10,
  timeoutMs: number = 10000
): Promise<WebhookRecentTransactionsResponse> {
  const url = `${normalizeUrl(baseUrl)}/webhooks/bank/recent?limit=${limit}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders({
        Accept: 'application/json',
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData?.detail) errorDetail = errorData.detail;
      } catch (_) {}
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Tiempo de espera agotado (${timeoutMs}ms) al consultar transacciones del webhook.`);
    }
    throw new Error(err.message || 'Error al obtener transacciones del webhook');
  }
}
