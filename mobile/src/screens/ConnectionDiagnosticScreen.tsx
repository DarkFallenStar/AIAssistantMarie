import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { DEFAULT_BACKEND_URL, DEFAULT_LAN_IP, DEFAULT_PORT } from '../config';
import { checkBackendHealth, sendChatMessage, HealthResponse, normalizeUrl } from '../services/api';

interface LogEntry {
  id: string;
  time: string;
  type: 'info' | 'success' | 'error';
  message: string;
}

export default function ConnectionDiagnosticScreen() {
  const [backendUrl, setBackendUrl] = useState<string>(DEFAULT_BACKEND_URL);
  const [isLoadingHealth, setIsLoadingHealth] = useState<boolean>(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Chat Test State (Fase 2)
  const [chatInput, setChatInput] = useState<string>('Hola');
  const [chatResponse, setChatResponse] = useState<string | null>(null);
  const [isSendingChat, setIsSendingChat] = useState<boolean>(false);

  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (type: 'info' | 'success' | 'error', message: string) => {
    const timeStr = new Date().toLocaleTimeString();
    setLogs((prev) => [
      { id: Math.random().toString(), time: timeStr, type, message },
      ...prev.slice(0, 15),
    ]);
  };

  const testHealth = async (targetUrl?: string) => {
    const urlToTest = normalizeUrl(targetUrl || backendUrl);
    setIsLoadingHealth(true);
    setHealthError(null);
    addLog('info', `GET ${urlToTest}/health ...`);

    try {
      const data = await checkBackendHealth(urlToTest);
      setHealthData(data);
      addLog('success', `Health OK (${data.latencyMs}ms): status = "${data.status}"`);
    } catch (err: any) {
      setHealthData(null);
      setHealthError(err.message);
      addLog('error', `Health Error: ${err.message}`);
    } finally {
      setIsLoadingHealth(false);
    }
  };

  const testChat = async () => {
    if (!chatInput.trim()) return;
    const urlToTest = normalizeUrl(backendUrl);
    setIsSendingChat(true);
    addLog('info', `POST ${urlToTest}/chat con: "${chatInput}" ...`);

    try {
      const reply = await sendChatMessage(urlToTest, chatInput);
      setChatResponse(reply);
      addLog('success', `Chat Responde: "${reply}"`);
    } catch (err: any) {
      addLog('error', `Chat Error: ${err.message}`);
    } finally {
      setIsSendingChat(false);
    }
  };

  useEffect(() => {
    testHealth();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#090d16" />
      <ScrollView contentContainerStyle={styles.container}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerSubtitle}>FASE 2 • BACKEND MÍNIMO</Text>
          <Text style={styles.headerTitle}>Personal Assistant AI</Text>
          <Text style={styles.headerDescription}>
            Pruebas de endpoints GET /health y POST /chat
          </Text>
        </View>

        {/* Health Status Card */}
        <View
          style={[
            styles.card,
            healthData
              ? styles.cardSuccess
              : healthError
              ? styles.cardError
              : styles.cardNeutral,
          ]}
        >
          <View style={styles.statusRow}>
            <View
              style={[
                styles.statusDot,
                healthData
                  ? styles.dotOnline
                  : isLoadingHealth
                  ? styles.dotPending
                  : styles.dotOffline,
              ]}
            />
            <Text style={styles.statusTitle}>
              {isLoadingHealth
                ? 'Comprobando GET /health...'
                : healthData
                ? `Backend Online (status: ${healthData.status})`
                : 'Backend Desconectado'}
            </Text>
            {healthData && (
              <View style={styles.latencyBadge}>
                <Text style={styles.latencyText}>{healthData.latencyMs} ms</Text>
              </View>
            )}
          </View>

          {healthError && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{healthError}</Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.refreshHealthBtn}
            onPress={() => testHealth()}
            disabled={isLoadingHealth}
          >
            <Text style={styles.refreshHealthText}>
              {isLoadingHealth ? 'Verificando...' : '↻ Reintentar GET /health'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* POST /chat Test Card */}
        <View style={styles.cardChat}>
          <Text style={styles.sectionTitle}>Prueba de Endpoint: POST /chat</Text>
          <Text style={styles.inputLabel}>Mensaje a enviar:</Text>
          
          <View style={styles.chatInputRow}>
            <TextInput
              style={styles.chatTextInput}
              value={chatInput}
              onChangeText={setChatInput}
              placeholder='Ej: "Hola"'
              placeholderTextColor="#64748b"
            />
            <TouchableOpacity
              style={[styles.sendChatBtn, isSendingChat && styles.buttonDisabled]}
              onPress={testChat}
              disabled={isSendingChat}
            >
              {isSendingChat ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.sendChatBtnText}>Enviar</Text>
              )}
            </TouchableOpacity>
          </View>

          {chatResponse && (
            <View style={styles.responseContainer}>
              <Text style={styles.responseLabel}>Respuesta del Servidor:</Text>
              <View style={styles.responseBubble}>
                <Text style={styles.responseText}>{chatResponse}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Server Config & IP Presets */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuración de Conexión</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={backendUrl}
              onChangeText={setBackendUrl}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="http://10.43.236.182:8000"
              placeholderTextColor="#64748b"
            />
          </View>

          <View style={styles.presetsRow}>
            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => {
                const url = `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;
                setBackendUrl(url);
                testHealth(url);
              }}
            >
              <Text style={styles.presetBtnText}>IP LAN ({DEFAULT_LAN_IP})</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => {
                const url = `http://10.0.2.2:${DEFAULT_PORT}`;
                setBackendUrl(url);
                testHealth(url);
              }}
            >
              <Text style={styles.presetBtnText}>Emulador (10.0.2.2)</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Live Logs */}
        <View style={styles.section}>
          <View style={styles.logHeaderRow}>
            <Text style={styles.sectionTitle}>Consola de Eventos</Text>
            <TouchableOpacity onPress={() => setLogs([])}>
              <Text style={styles.clearLogsText}>Limpiar</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.consoleBox}>
            {logs.length === 0 ? (
              <Text style={styles.consoleEmpty}>Sin eventos registrados</Text>
            ) : (
              logs.map((log) => (
                <View key={log.id} style={styles.logRow}>
                  <Text style={styles.logTime}>[{log.time}]</Text>
                  <Text
                    style={[
                      styles.logMessage,
                      log.type === 'success'
                        ? styles.logSuccess
                        : log.type === 'error'
                        ? styles.logError
                        : styles.logInfo,
                    ]}
                  >
                    {log.message}
                  </Text>
                </View>
              ))
            )}
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 18,
  },
  headerSubtitle: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  headerTitle: {
    color: '#f8fafc',
    fontSize: 24,
    fontWeight: '800',
  },
  headerDescription: {
    color: '#94a3b8',
    fontSize: 13,
    marginTop: 4,
  },
  card: {
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  cardNeutral: {
    backgroundColor: '#1e293b',
    borderColor: '#334155',
  },
  cardSuccess: {
    backgroundColor: '#06281e',
    borderColor: '#059669',
  },
  cardError: {
    backgroundColor: '#2b1117',
    borderColor: '#e11d48',
  },
  cardChat: {
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  dotOnline: {
    backgroundColor: '#10b981',
  },
  dotPending: {
    backgroundColor: '#f59e0b',
  },
  dotOffline: {
    backgroundColor: '#ef4444',
  },
  statusTitle: {
    color: '#f8fafc',
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
  },
  latencyBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#10b981',
  },
  latencyText: {
    color: '#34d399',
    fontSize: 11,
    fontWeight: '600',
  },
  refreshHealthBtn: {
    marginTop: 10,
    paddingVertical: 6,
    alignItems: 'center',
  },
  refreshHealthText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  errorBox: {
    marginTop: 8,
  },
  errorText: {
    color: '#fb7185',
    fontSize: 12,
  },
  sectionTitle: {
    color: '#f8fafc',
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 10,
  },
  inputLabel: {
    color: '#94a3b8',
    fontSize: 12,
    marginBottom: 6,
  },
  chatInputRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  chatTextInput: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
    color: '#f8fafc',
    paddingHorizontal: 12,
    height: 42,
    fontSize: 14,
  },
  sendChatBtn: {
    backgroundColor: '#0284c7',
    borderRadius: 10,
    paddingHorizontal: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendChatBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  responseContainer: {
    marginTop: 8,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  responseLabel: {
    color: '#64748b',
    fontSize: 11,
    marginBottom: 6,
  },
  responseBubble: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#38bdf8',
  },
  responseText: {
    color: '#e2e8f0',
    fontSize: 14,
    lineHeight: 20,
  },
  section: {
    marginBottom: 20,
  },
  inputContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    marginBottom: 10,
  },
  input: {
    color: '#f8fafc',
    height: 42,
    fontSize: 13,
  },
  presetsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  presetBtn: {
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#475569',
  },
  presetBtnText: {
    color: '#cbd5e1',
    fontSize: 11,
    fontWeight: '500',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  logHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  clearLogsText: {
    color: '#64748b',
    fontSize: 12,
  },
  consoleBox: {
    backgroundColor: '#020617',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 12,
    minHeight: 110,
  },
  consoleEmpty: {
    color: '#475569',
    fontSize: 12,
    fontStyle: 'italic',
  },
  logRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  logTime: {
    color: '#64748b',
    fontSize: 11,
    marginRight: 6,
  },
  logMessage: {
    flex: 1,
    fontSize: 11,
  },
  logInfo: {
    color: '#94a3b8',
  },
  logSuccess: {
    color: '#34d399',
  },
  logError: {
    color: '#f87171',
  },
});
