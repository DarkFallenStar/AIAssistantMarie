/**
 * Default backend connection settings.
 * In development with Android / Expo Go, localhost points to the phone itself,
 * so we default to the computer's LAN IP or Tailscale IP.
 */
export const DEFAULT_LAN_IP = "192.168.40.15";
export const DEFAULT_TAILSCALE_IP = "100.95.54.56"; // Assigned Tailscale IP of Windows backend laptop
export const DEFAULT_PORT = "8000";
export const DEFAULT_BACKEND_URL = `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;
export const DEFAULT_TAILSCALE_URL = `http://${DEFAULT_TAILSCALE_IP}:${DEFAULT_PORT}`;

export const STORAGE_KEYS = {
  BACKEND_URL: "assistant_backend_url",
  LAST_CONNECTED: "assistant_last_connected",
  CONNECTION_MODE: "assistant_connection_mode",
  TAILSCALE_IP: "assistant_tailscale_ip",
};
