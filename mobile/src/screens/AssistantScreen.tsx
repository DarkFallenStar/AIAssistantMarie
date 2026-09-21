import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Keyboard,
  TouchableWithoutFeedback,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  useAudioRecorder,
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorderState,
} from 'expo-audio';
import * as Speech from 'expo-speech';
import StatusBadge, { AssistantState } from '../components/StatusBadge';
import MessageList from '../components/MessageList';
import { ChatMessage } from '../components/MessageBubble';
import MicButton from '../components/MicButton';
import { DEFAULT_BACKEND_URL } from '../config';
import { sendChatMessage, sendAudioRecording } from '../services/api';

interface AssistantScreenProps {
  backendUrl?: string;
  onOpenDiagnostics?: () => void;
}

/**
 * Strips markdown symbols (bold, italic, headers, backticks, bullet asterisks)
 * so that TTS synthesizes smooth, natural speech without reading characters like '*' or '#'.
 */
function stripMarkdownForTTS(text: string): string {
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

export default function AssistantScreen({
  backendUrl = DEFAULT_BACKEND_URL,
  onOpenDiagnostics,
}: AssistantScreenProps) {
  const [state, setState] = useState<AssistantState>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTTSActive, setIsTTSActive] = useState<boolean>(true);

  // Inicializar grabador nativo de Expo Audio SDK 57
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const recorderState = useAudioRecorderState(audioRecorder);

  useEffect(() => {
    (async () => {
      try {
        await setAudioModeAsync({
          playsInSilentMode: true,
          allowsRecording: true,
        });
      } catch (err) {
        console.warn('Error configurando modo de audio inicial:', err);
      }
    })();

    return () => {
      Speech.stop();
    };
  }, []);

  const getFormattedTime = () => {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isRecording = state === 'RECORDING' || state === 'grabando';
  const isProcessing = state === 'PROCESSING' || state === 'procesando';

  const speakResponse = (text: string) => {
    if (!isTTSActive || !text || !text.trim()) return;
    const clean = stripMarkdownForTTS(text);
    Speech.stop();
    Speech.speak(clean, {
      language: 'es-ES',
      rate: 1.0,
      pitch: 1.0,
    });
  };

  const handleSendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isProcessing) return;

    // Detener cualquier audio previo antes de procesar el nuevo mensaje
    Speech.stop();
    setErrorMessage(null);

    // 1. Mensaje del usuario
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: 'user',
      text: trimmed,
      timestamp: getFormattedTime(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');

    // 2. Estado PROCESSING
    setState('PROCESSING');

    try {
      // 3. POST /chat
      const reply = await sendChatMessage(backendUrl, trimmed);

      // 4. Estado RESPONSE
      setState('RESPONSE');
      const assistantMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: reply,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // 5. Síntesis Text To Speech (TTS) para que el usuario escuche la respuesta
      speakResponse(reply);

      // 6. Retorno a IDLE
      setTimeout(() => {
        setState('IDLE');
      }, 1800);
    } catch (err: any) {
      setState('IDLE');
      const errText = err.message || 'Error al conectar con el servidor';
      setErrorMessage(errText);

      const errorMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: `⚠️ No se pudo obtener respuesta del backend. Verifica que el servidor esté encendido en ${backendUrl}.`,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleMicPress = async () => {
    // Detener cualquier audio previo
    Speech.stop();

    if (!isRecording) {
      // 1. Solicitar permiso de grabación de audio nativo
      const permissionStatus = await AudioModule.requestRecordingPermissionsAsync();
      if (!permissionStatus.granted) {
        Alert.alert(
          'Permiso de Micrófono Denegado',
          'Se requiere acceso al micrófono para capturar tus comandos de voz. Por favor concede el permiso en la configuración de Android.',
          [{ text: 'Entendido' }]
        );
        return;
      }

      try {
        setErrorMessage(null);
        await setAudioModeAsync({
          playsInSilentMode: true,
          allowsRecording: true,
        });

        // 2. Preparar e iniciar grabación
        await audioRecorder.prepareToRecordAsync();
        audioRecorder.record();

        // 3. Transición a RECORDING
        setState('RECORDING');
      } catch (err: any) {
        setErrorMessage(`No se pudo iniciar la grabación: ${err.message}`);
        setState('IDLE');
      }
    } else {
      // 4. Usuario termina la grabación
      try {
        setState('PROCESSING');
        await audioRecorder.stop();

        const audioUri = audioRecorder.uri;
        if (!audioUri) {
          throw new Error('No se generó el archivo de audio local.');
        }

        // 5. Mostrar en el chat indicador de transcripción
        const userMsgId = Math.random().toString();
        const userMsg: ChatMessage = {
          id: userMsgId,
          sender: 'user',
          text: '🎙️ Transcribiendo audio...',
          timestamp: getFormattedTime(),
        };
        setMessages((prev) => [...prev, userMsg]);

        // 6. Enviar audio binario al backend POST /voice vía multipart/form-data
        const voiceResult = await sendAudioRecording(backendUrl, audioUri);

        // Actualizar burbuja del usuario con el texto transcrito por STT
        if (voiceResult.transcribed_text && voiceResult.transcribed_text.trim()) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === userMsgId
                ? { ...msg, text: `🎙️ "${voiceResult.transcribed_text}"` }
                : msg
            )
          );
        } else {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === userMsgId
                ? { ...msg, text: '🎙️ [Audio sin voz detectable]' }
                : msg
            )
          );
        }

        // 7. Transición a RESPONSE
        setState('RESPONSE');

        const assistantMsg: ChatMessage = {
          id: Math.random().toString(),
          sender: 'assistant',
          text: voiceResult.response,
          timestamp: getFormattedTime(),
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // 8. Síntesis Text To Speech (TTS) para escuchar la respuesta
        speakResponse(voiceResult.response);

        // 9. Retorno a IDLE
        setTimeout(() => {
          setState('IDLE');
        }, 2500);
      } catch (err: any) {
        setState('IDLE');
        const errText = err.message || 'Error al procesar el audio';
        setErrorMessage(errText);

        const errorMsg: ChatMessage = {
          id: Math.random().toString(),
          sender: 'assistant',
          text: `⚠️ Error en captura/envío de audio: ${errText}`,
          timestamp: getFormattedTime(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    }
  };

  const handleCancelRecording = async () => {
    Speech.stop();
    if (!isRecording) return;
    try {
      await audioRecorder.stop();
    } catch (err: any) {
      console.warn('Error al detener grabación cancelada:', err);
    } finally {
      setState('IDLE');
      setErrorMessage(null);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#090d16" />
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Top Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Text style={styles.headerTitle}>Personal Assistant</Text>
            <View style={styles.serverPill}>
              <View style={styles.serverDot} />
              <Text style={styles.serverUrlText} numberOfLines={1}>
                {backendUrl}
              </Text>
            </View>
          </View>

          <View style={styles.headerRight}>
            <TouchableOpacity
              style={[styles.ttsToggleButton, isTTSActive ? styles.ttsActiveBtn : styles.ttsMutedBtn]}
              onPress={() => {
                if (isTTSActive) {
                  Speech.stop();
                }
                setIsTTSActive((prev) => !prev);
              }}
              activeOpacity={0.7}
              accessibilityLabel={isTTSActive ? "Desactivar síntesis de voz" : "Activar síntesis de voz"}
            >
              <Text style={styles.ttsToggleText}>{isTTSActive ? '🔊 Voz' : '🔇 Mute'}</Text>
            </TouchableOpacity>

            {onOpenDiagnostics && (
              <TouchableOpacity
                style={styles.diagButton}
                onPress={onOpenDiagnostics}
                activeOpacity={0.7}
              >
                <Text style={styles.diagButtonText}>⚙️ Red</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* State Indicator Banner */}
        <View style={styles.stateBar}>
          <StatusBadge state={state} />
        </View>

        {/* Error Banner */}
        {errorMessage && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText} numberOfLines={2}>
              {errorMessage}
            </Text>
          </View>
        )}

        {/* Conversation Area (Message List) */}
        <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
          <View style={styles.chatArea}>
            <MessageList messages={messages} onSpeak={(text) => speakResponse(text)} />
          </View>
        </TouchableWithoutFeedback>

        {/* Recording Notice */}
        {isRecording && (
          <View style={styles.recordingNotice}>
            <Text style={styles.recordingNoticeText} numberOfLines={1}>
              🔴 Grabando audio...
            </Text>
            <TouchableOpacity
              style={styles.cancelNoticeBtn}
              onPress={handleCancelRecording}
              activeOpacity={0.7}
            >
              <Text style={styles.cancelNoticeBtnText}>✕ Cancelar</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Bottom Control Section */}
        <View style={styles.bottomSection}>
          {/* Text Input Row */}
          <View style={styles.inputRow}>
            <TextInput
              style={styles.textInput}
              placeholder="Escribe o pulsa el micrófono para hablar..."
              placeholderTextColor="#6b7280"
              value={inputText}
              onChangeText={setInputText}
              onSubmitEditing={() => handleSendMessage(inputText)}
              returnKeyType="send"
              editable={!isProcessing}
            />
            {inputText.trim().length > 0 && (
              <TouchableOpacity
                style={[
                  styles.sendButton,
                  isProcessing && styles.sendButtonDisabled,
                ]}
                onPress={() => handleSendMessage(inputText)}
                disabled={isProcessing}
              >
                <Text style={styles.sendButtonText}>➤</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Mic Button Row */}
          <View style={styles.micRow}>
            {isRecording && (
              <TouchableOpacity
                style={styles.cancelRoundBtn}
                onPress={handleCancelRecording}
                activeOpacity={0.7}
              >
                <Text style={styles.cancelRoundBtnIcon}>✕</Text>
                <Text style={styles.cancelRoundBtnSub}>Cancelar</Text>
              </TouchableOpacity>
            )}

            <MicButton
              state={state}
              onPress={handleMicPress}
              disabled={isProcessing}
            />

            {isRecording && <View style={styles.roundPlaceholder} />}
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  headerLeft: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#f8fafc',
    letterSpacing: 0.3,
  },
  serverPill: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 3,
    backgroundColor: '#111827',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  serverDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981',
    marginRight: 6,
  },
  serverUrlText: {
    fontSize: 10,
    color: '#94a3b8',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ttsToggleButton: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
  },
  ttsActiveBtn: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: '#10b981',
  },
  ttsMutedBtn: {
    backgroundColor: 'rgba(107, 114, 128, 0.15)',
    borderColor: '#6b7280',
  },
  ttsToggleText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#e5e7eb',
  },
  diagButton: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  diagButtonText: {
    fontSize: 12,
    color: '#e2e8f0',
    fontWeight: '600',
  },
  stateBar: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  errorBanner: {
    backgroundColor: '#450a0a',
    marginHorizontal: 16,
    marginBottom: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#991b1b',
  },
  errorBannerText: {
    color: '#fca5a5',
    fontSize: 12,
    textAlign: 'center',
  },
  chatArea: {
    flex: 1,
  },
  recordingNotice: {
    backgroundColor: '#271216',
    borderTopWidth: 1,
    borderTopColor: '#7f1d1d',
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  recordingNoticeText: {
    color: '#f87171',
    fontSize: 12,
    fontWeight: '700',
    flex: 1,
  },
  cancelNoticeBtn: {
    backgroundColor: '#451a1a',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#991b1b',
    marginLeft: 8,
  },
  cancelNoticeBtnText: {
    color: '#fca5a5',
    fontSize: 12,
    fontWeight: '700',
  },
  cancelRoundBtn: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#271216',
    borderWidth: 1.5,
    borderColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 18,
  },
  cancelRoundBtnIcon: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: 'bold',
    lineHeight: 18,
  },
  cancelRoundBtnSub: {
    color: '#fca5a5',
    fontSize: 9,
    fontWeight: '600',
  },
  roundPlaceholder: {
    width: 50,
    height: 50,
    marginLeft: 18,
  },
  bottomSection: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    backgroundColor: '#0c111d',
    alignItems: 'center',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: 8,
    gap: 8,
  },
  textInput: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#f8fafc',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#334155',
  },
  sendButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  micRow: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
