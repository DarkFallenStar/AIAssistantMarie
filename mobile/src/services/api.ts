export interface HealthResponse {
  status: string;
  latencyMs: number;
}

export interface ChatResponse {
  response: string;
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
 * Sends a chat message to POST /chat and returns the response string.
 */
export async function sendChatMessage(
  baseUrl: string,
  message: string,
  timeoutMs: number = 10000
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
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Tiempo de espera agotado (${timeoutMs}ms) al enviar el mensaje.`);
    }
    throw new Error(err.message || "Error al comunicarse con /chat");
  }
}
