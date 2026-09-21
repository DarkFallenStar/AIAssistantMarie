import unittest
import io
from starlette.testclient import TestClient
from app.main import app
from app.audio.stt import MockSTTService, set_stt_service
from app.services.llm import MockLLMService, set_llm_service

class TestVoiceEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_stt = MockSTTService("Audio de prueba recibido")
        set_stt_service(self.mock_stt)
        self.mock_llm = MockLLMService(canned_response="Audio de prueba recibido con exito.")
        set_llm_service(self.mock_llm)

    def tearDown(self):
        set_stt_service(None)
        set_llm_service(None)

    def test_upload_voice_valid(self):
        fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....test_audio_bytes")
        fake_audio.name = "recording.m4a"
        
        response = self.client.post(
            "/voice",
            files={"file": ("recording.m4a", fake_audio, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["filename"], "recording.m4a")
        self.assertGreater(data["size_bytes"], 0)
        self.assertEqual(data["transcribed_text"], "Audio de prueba recibido")
        self.assertIn("Audio de prueba recibido", data["response"])

    def test_upload_voice_empty_file(self):
        empty_audio = io.BytesIO(b"")
        response = self.client.post(
            "/voice",
            files={"file": ("empty.m4a", empty_audio, "audio/m4a")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("vacio", response.json()["detail"].lower())

if __name__ == "__main__":
    unittest.main()
