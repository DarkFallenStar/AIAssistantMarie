import unittest
from pathlib import Path
from starlette.testclient import TestClient
from app.main import app
from app.audio.tts import MockTTSService, get_tts_service, set_tts_service, TTS_DIR


class TestTTSService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.tts = MockTTSService()
        set_tts_service(self.tts)

    def tearDown(self):
        set_tts_service(None)

    def test_mock_tts_synthesis_creates_valid_file(self):
        path = self.tts.synthesize("Hola, esta es una prueba de sintesis de voz.")
        self.assertTrue(path.exists())
        self.assertTrue(path.is_file())
        self.assertGreater(path.stat().st_size, 100)
        # Verify WAV header
        with open(path, "rb") as f:
            header = f.read(4)
            self.assertEqual(header, b"RIFF")

    def test_mock_tts_empty_text_raises_error(self):
        with self.assertRaises(ValueError):
            self.tts.synthesize("")
        with self.assertRaises(ValueError):
            self.tts.synthesize("   ")

    def test_post_tts_endpoint_returns_binary_wav(self):
        response = self.client.post(
            "/tts",
            json={"text": "Respuesta sintetizada para la aplicacion movil", "voice": "es"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "audio/wav")
        self.assertGreater(len(response.content), 100)
        self.assertTrue(response.content.startswith(b"RIFF"))

    def test_post_tts_endpoint_as_json(self):
        response = self.client.post(
            "/tts?as_json=true",
            json={"text": "Generando enlace estatico de audio", "voice": "es"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("/static/audio/tts/", data["audio_url"])
        self.assertEqual(data["text"], "Generando enlace estatico de audio")

    def test_post_tts_endpoint_empty_text_rejected(self):
        response = self.client.post(
            "/tts",
            json={"text": "   "}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("vac", response.json()["detail"].lower())

    def test_get_tts_audio_file(self):
        # Generate a test audio file
        path = self.tts.synthesize("Audio de prueba para descarga")
        filename = path.name

        response = self.client.get(f"/tts/{filename}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "audio/wav")
        self.assertGreater(len(response.content), 50)

    def test_get_tts_audio_non_existent(self):
        response = self.client.get("/tts/archivo_inexistente_xyz_123.wav")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
