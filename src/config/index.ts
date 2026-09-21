/**
 * Default backend connection & security settings.
 * In development with Android / Expo Go, localhost points to the phone itself,
 * so we default to the computer's LAN IP or Tailscale IP.
 */
export const DEFAULT_LAN_IP = "192.168.40.15";
export const DEFAULT_TAILSCALE_IP = process.env.EXPO_PUBLIC_TAILSCALE_IP || "100.95.54.56";
export const DEFAULT_PORT = "8000";
export const DEFAULT_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;
export const DEFAULT_TAILSCALE_URL = `http://${DEFAULT_TAILSCALE_IP}:${DEFAULT_PORT}`;

// Security credentials (loaded from environment or storage)
export const DEFAULT_API_TOKEN = process.env.EXPO_PUBLIC_API_TOKEN || "";
export const DEFAULT_BANK_WEBHOOK_SECRET = process.env.EXPO_PUBLIC_BANK_WEBHOOK_SECRET || "";

export const STORAGE_KEYS = {
  BACKEND_URL: "assistant_backend_url",
  LAST_CONNECTED: "assistant_last_connected",
  CONNECTION_MODE: "assistant_connection_mode",
  TAILSCALE_IP: "assistant_tailscale_ip",
  API_TOKEN: "assistant_api_token",
  BANK_WEBHOOK_SECRET: "assistant_bank_webhook_secret",
};
