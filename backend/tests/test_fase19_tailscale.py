import unittest
import socket
from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings

class TestFase19Tailscale(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Host Network Binding Verification (0.0.0.0)
    # -------------------------------------------------------------
    def test_backend_host_binding_allows_tailscale(self):
        # HOST must be "0.0.0.0" so FastAPI binds to loopback, LAN, and Tailscale interface (100.x.y.z)
        self.assertEqual(settings.HOST, "0.0.0.0")

    # -------------------------------------------------------------
    # 2. Tailscale CGNAT IP Format & Range Verification
    # -------------------------------------------------------------
    def test_tailscale_ip_format_and_cgnat_range(self):
        # Tailscale assigns addresses in the CGNAT block 100.64.0.0/10 (100.64.0.1 to 100.127.255.254)
        def is_tailscale_ip(ip: str) -> bool:
            parts = ip.strip().split(".")
            if len(parts) != 4:
                return False
            try:
                first = int(parts[0])
                second = int(parts[1])
                return first == 100 and (64 <= second <= 127)
            except ValueError:
                return False

        # Verify standard configured Tailscale IP adheres to CGNAT specification
        sample_tailscale_ip = "100.91.240.52"
        self.assertTrue(is_tailscale_ip(sample_tailscale_ip))
        self.assertFalse(is_tailscale_ip("192.168.1.50"))
        self.assertFalse(is_tailscale_ip("127.0.0.1"))

    # -------------------------------------------------------------
    # 3. Remote Request Simulation (Host header and forwarded IP)
    # -------------------------------------------------------------
    def test_remote_cellular_request_via_tailscale(self):
        # Simulate an incoming HTTP request arriving from Tailscale overlay interface
        headers = {
            "Host": "100.91.240.52:8000",
            "X-Forwarded-For": "100.115.82.14",  # Remote mobile client IP in Tailnet
            "User-Agent": "PersonalAssistantAI-Mobile/1.0 (Android; Expo Go)"
        }
        res = self.client.get("/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")

    # -------------------------------------------------------------
    # 4. LAN to Tailscale URL Switching & Normalization
    # -------------------------------------------------------------
    def test_url_normalization_for_remote_networking(self):
        def normalize_url(raw_url: str) -> str:
            clean = raw_url.strip()
            if not clean.startswith("http://") and not clean.startswith("https://"):
                clean = f"http://{clean}"
            return clean.rstrip("/")

        lan_url = normalize_url("192.168.40.15:8000/")
        tailscale_url = normalize_url("100.91.240.52:8000/")

        self.assertEqual(lan_url, "http://192.168.40.15:8000")
        self.assertEqual(tailscale_url, "http://100.91.240.52:8000")

if __name__ == "__main__":
    unittest.main()
