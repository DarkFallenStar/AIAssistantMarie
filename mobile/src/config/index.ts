/**
 * Default backend connection settings.
 * In development with Android / Expo Go, localhost points to the phone itself,
 * so we default to the computer's LAN IP or Tailscale IP.
 */
export const DEFAULT_LAN_IP = "10.43.236.182";
export const DEFAULT_PORT = "8000";
export const DEFAULT_BACKEND_URL = `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;

export const STORAGE_KEYS = {
  BACKEND_URL: "assistant_backend_url",
  LAST_CONNECTED: "assistant_last_connected",
};
