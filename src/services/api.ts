export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  llm_provider: string;
  llm_model: string;
  latencyMs: number;
}

export function normalizeUrl(url: string): string {
  let clean = url.trim();
  if (!clean.startsWith("http://") && !clean.startsWith("https://")) {
    clean = `http://${clean}`;
  }
  return clean.replace(/\/+$/, "");
}

/**
 * Checks connectivity with the FastAPI backend health endpoint.
 * Measures response round-trip latency.
 */
export async function checkBackendHealth(
  baseUrl: string,
  timeoutMs: number = 5000
): Promise<HealthResponse> {
  const url = `${normalizeUrl(baseUrl)}/api/health`;
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
      ...data,
      latencyMs,
    };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Connection timed out after ${timeoutMs}ms. Verify that the backend is running and reachable.`);
    }
    throw new Error(err.message || "Failed to reach backend server");
  }
}
