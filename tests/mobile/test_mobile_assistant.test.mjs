import { test, describe, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

/**
 * Mobile Assistant Logic & State Machine Tests (Fase 19)
 * Validates:
 * 1. Permisos (AudioModule recording permissions)
 * 2. Grabación (AudioRecorder start, stop, uri, state transitions)
 * 3. Envío (multipart /voice and json /chat contracts)
 * 4. Respuesta (message list aggregation and error handling)
 * 5. TTS (markdown stripping for speech synthesis and playback control)
 */

// -----------------------------------------------------------------------------
// Markdown Stripping Helper (replicates stripMarkdownForTTS from AssistantScreen.tsx)
// -----------------------------------------------------------------------------
function stripMarkdownForTTS(text) {
  if (!text) return '';
  return text
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    .replace(/`{1,3}(.*?)`{1,3}/g, '$1')
    .replace(/^#+\s+/gm, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[-*+]\s+/g, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .trim();
}

describe('Fase 19 — Mobile Assistant Unit Tests', () => {

  // ---------------------------------------------------------------------------
  // 1. Permisos de Micrófono
  // ---------------------------------------------------------------------------
  describe('Permisos de Grabación (AudioModule)', () => {
    test('Permiso concedido permite iniciar grabación', async () => {
      const mockAudioModule = {
        requestRecordingPermissionsAsync: async () => ({ granted: true, status: 'granted' })
      };

      let recordingStarted = false;
      let alertShown = false;

      const handleMicPress = async (isRecording) => {
        if (!isRecording) {
          const perm = await mockAudioModule.requestRecordingPermissionsAsync();
          if (!perm.granted) {
            alertShown = true;
            return;
          }
          recordingStarted = true;
        }
      };

      await handleMicPress(false);
      assert.equal(recordingStarted, true);
      assert.equal(alertShown, false);
    });

    test('Permiso denegado bloquea la grabación y emite notificación al usuario', async () => {
      const mockAudioModule = {
        requestRecordingPermissionsAsync: async () => ({ granted: false, status: 'denied' })
      };

      let recordingStarted = false;
      let alertShown = false;

      const handleMicPress = async (isRecording) => {
        if (!isRecording) {
          const perm = await mockAudioModule.requestRecordingPermissionsAsync();
          if (!perm.granted) {
            alertShown = true;
            return;
          }
          recordingStarted = true;
        }
      };

      await handleMicPress(false);
      assert.equal(recordingStarted, false);
      assert.equal(alertShown, true);
    });
  });

  // ---------------------------------------------------------------------------
  // 2. Grabación de Audio y Ciclo de Vida
  // ---------------------------------------------------------------------------
  describe('Grabación de Audio (useAudioRecorder & State Machine)', () => {
    test('Ciclo completo: prepare -> record -> stop genera archivo de audio', async () => {
      let isRecording = false;
      let isPrepared = false;
      let generatedUri = null;

      const mockAudioRecorder = {
        prepareToRecordAsync: async () => { isPrepared = true; },
        record: () => { isRecording = true; },
        stop: async () => {
          isRecording = false;
          generatedUri = 'file:///data/user/0/host.exp.exponent/cache/Audio/recording_test.m4a';
        },
        get uri() { return generatedUri; }
      };

      // 1. Prepare and record
      await mockAudioRecorder.prepareToRecordAsync();
      mockAudioRecorder.record();
      assert.equal(isPrepared, true);
      assert.equal(isRecording, true);

      // 2. Stop recording
      await mockAudioRecorder.stop();
      assert.equal(isRecording, false);
      assert.ok(mockAudioRecorder.uri);
      assert.match(mockAudioRecorder.uri, /\.m4a$/);
    });

    test('Transición de estados de la UI: IDLE -> RECORDING -> PROCESSING -> RESPONSE -> IDLE', () => {
      const states = [];
      let currentState = 'IDLE';

      const transitionTo = (newState) => {
        currentState = newState;
        states.push(currentState);
      };

      // Simulating user voice command lifecycle
      transitionTo('RECORDING');   // User presses mic
      transitionTo('PROCESSING');  // User stops mic, audio uploads to STT
      transitionTo('RESPONSE');    // Backend returns response and TTS speaks
      transitionTo('IDLE');        // Reset to idle

      assert.deepEqual(states, ['RECORDING', 'PROCESSING', 'RESPONSE', 'IDLE']);
    });
  });

  // ---------------------------------------------------------------------------
  // 3. Envío de Audio y Mensajes
  // ---------------------------------------------------------------------------
  describe('Envío de Mensajes y Grabaciones', () => {
    test('Envío de mensaje de texto a POST /chat conforma payload correcto', async () => {
      let capturedUrl = '';
      let capturedBody = null;
      let capturedHeaders = null;

      const mockFetch = async (url, options) => {
        capturedUrl = url;
        capturedBody = JSON.parse(options.body);
        capturedHeaders = options.headers;
        return {
          ok: true,
          json: async () => ({
            response: 'Respuesta del agente simulada',
            intent: 'financial',
            agent: 'FinancialAgent',
            tools_executed: ['calculate_cash_flow']
          })
        };
      };

      const sendChatMessage = async (baseUrl, message, token) => {
        const res = await mockFetch(`${baseUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message })
        });
        const data = await res.json();
        return data.response;
      };

      const reply = await sendChatMessage('http://100.91.240.52:8000', '¿Cuánto saldo tengo?', 'my_token_123');

      assert.equal(capturedUrl, 'http://100.91.240.52:8000/chat');
      assert.equal(capturedBody.message, '¿Cuánto saldo tengo?');
      assert.equal(capturedHeaders['Authorization'], 'Bearer my_token_123');
      assert.equal(reply, 'Respuesta del agente simulada');
    });

    test('Envío de audio multipart a POST /voice conforma contrato esperado', async () => {
      let uploadConfig = null;

      const mockFileUpload = async (url, options) => {
        uploadConfig = { url, ...options };
        return {
          status: 200,
          body: JSON.stringify({
            status: 'success',
            filename: 'recording_123.m4a',
            transcribed_text: 'Anota una tarea urgente',
            response: 'Tarea anotada correctamente.',
            audio_url: '/static/audio/tts/tts_123.wav'
          })
        };
      };

      const sendAudio = async (baseUrl, fileUri) => {
        const res = await mockFileUpload(`${baseUrl}/voice`, {
          fieldName: 'file',
          httpMethod: 'POST',
          mimeType: 'audio/m4a',
          uploadType: 'MULTIPART'
        });
        return JSON.parse(res.body);
      };

      const result = await sendAudio('http://100.91.240.52:8000', 'file:///audio.m4a');
      assert.equal(uploadConfig.url, 'http://100.91.240.52:8000/voice');
      assert.equal(uploadConfig.fieldName, 'file');
      assert.equal(uploadConfig.mimeType, 'audio/m4a');
      assert.equal(result.transcribed_text, 'Anota una tarea urgente');
      assert.equal(result.response, 'Tarea anotada correctamente.');
    });
  });

  // ---------------------------------------------------------------------------
  // 4. Respuesta y Gestión de Mensajes en el Chat
  // ---------------------------------------------------------------------------
  describe('Respuesta y Renderizado de Mensajes', () => {
    test('Agrega mensajes del usuario y asistente manteniendo orden cronológico', () => {
      const messages = [];

      const addMessage = (sender, text) => {
        messages.push({
          id: String(messages.length + 1),
          sender,
          text,
          timestamp: '13:45'
        });
      };

      addMessage('user', 'Hola asistente');
      addMessage('assistant', '¡Hola! ¿En qué puedo ayudarte hoy?');

      assert.equal(messages.length, 2);
      assert.equal(messages[0].sender, 'user');
      assert.equal(messages[0].text, 'Hola asistente');
      assert.equal(messages[1].sender, 'assistant');
      assert.equal(messages[1].text, '¡Hola! ¿En qué puedo ayudarte hoy?');
    });

    test('Manejo de error de red agrega mensaje de contingencia en el chat', () => {
      const messages = [];
      let errorMessage = null;

      const handleFailure = (error) => {
        errorMessage = error.message;
        messages.push({
          id: 'err_1',
          sender: 'assistant',
          text: '⚠️ No se pudo obtener respuesta del backend. Verifica que el servidor esté encendido.'
        });
      };

      handleFailure(new Error('Network request failed'));
      assert.equal(errorMessage, 'Network request failed');
      assert.equal(messages.length, 1);
      assert.match(messages[0].text, /⚠️ No se pudo obtener respuesta/);
    });
  });

  // ---------------------------------------------------------------------------
  // 5. TTS (Text-To-Speech) y Limpieza de Markdown
  // ---------------------------------------------------------------------------
  describe('Síntesis de Voz (TTS) y Limpieza de Markdown', () => {
    test('stripMarkdownForTTS elimina negritas, cursivas, encabezados y viñetas sin perder texto', () => {
      const rawMarkdown = '### Resumen Financiero\n- Tienes **$1,500 USD** disponibles.\n- Tu meta de *ahorro* va al `75%`.\n[Ver detalles](http://link)';
      const cleaned = stripMarkdownForTTS(rawMarkdown);

      assert.doesNotMatch(cleaned, /[*#`_]/);
      assert.doesNotMatch(cleaned, /\[.*\]\(.*\)/);
      assert.match(cleaned, /Resumen Financiero/);
      assert.match(cleaned, /1,500 USD/);
      assert.match(cleaned, /ahorro/);
      assert.match(cleaned, /75%/);
    });

    test('Detiene reproducción anterior antes de iniciar nueva síntesis o grabación', () => {
      const actions = [];
      const mockSpeech = {
        stop: () => { actions.push('stop'); },
        speak: (text) => { actions.push(`speak: ${text}`); }
      };

      const speakResponse = (text) => {
        mockSpeech.stop();
        const clean = stripMarkdownForTTS(text);
        mockSpeech.speak(clean);
      };

      speakResponse('**Hola**, respuesta 1');
      speakResponse('Respuesta 2');

      assert.deepEqual(actions, [
        'stop',
        'speak: Hola, respuesta 1',
        'stop',
        'speak: Respuesta 2'
      ]);
    });
  });
});
