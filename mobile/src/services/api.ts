import { File, UploadType } from 'expo-file-system';

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

export function normalizeUrl(url: string): string {
  let clean = url.trim();
  if (!clean.startsWith("http://") && !clean.startsWith("https://")) {
    clean = `http://${clean}`;
  }
  return clean.replace(/\/+$/, "");
}

/**
 * Checks connectivity with the FastAPI backend health endpoint (GET /health).
 * Measures response round-trip latency.
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
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
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
