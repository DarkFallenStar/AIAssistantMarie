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
import { checkBackendHealth, HealthResponse, normalizeUrl } from '../services/api';

interface LogEntry {
  id: string;
  time: string;
  type: 'info' | 'success' | 'error';
  message: string;
}

export default function ConnectionDiagnosticScreen() {
  const [backendUrl, setBackendUrl] = useState<string>(DEFAULT_BACKEND_URL);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (type: 'info' | 'success' | 'error', message: string) => {
    const timeStr = new Date().toLocaleTimeString();
    setLogs((prev) => [
      { id: Math.random().toString(), time: timeStr, type, message },
      ...prev.slice(0, 15), // keep last 15 logs
    ]);
  };

  const testConnection = async (targetUrl?: string) => {
    const urlToTest = normalizeUrl(targetUrl || backendUrl);
    setIsLoading(true);
    setErrorMsg(null);
    addLog('info', `Conectando con: ${urlToTest}/api/health ...`);

    try {
      const data = await checkBackendHealth(urlToTest);
      setHealthData(data);
      addLog('success', `Conexión exitosa (${data.latencyMs}ms) - Servidor: ${data.service} v${data.version}`);
    } catch (err: any) {
      setHealthData(null);
      setErrorMsg(err.message);
      addLog('error', `Fallo de conexión: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Auto test on initial render
    testConnection();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#0f172a" />
      <ScrollView contentContainerStyle={styles.container}>
        
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerSubtitle}>FASE 1 • ARQUITECTURA BASE</Text>
          <Text style={styles.headerTitle}>Personal Assistant AI</Text>
          <Text style={styles.headerDescription}>
            Diagnóstico de conectividad móvil ↔ backend
          </Text>
        </View>

        {/* Status Card */}
        <View
          style={[
            styles.card,
            healthData
              ? styles.cardSuccess
              : errorMsg
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
                  : isLoading
                  ? styles.dotPending
                  : styles.dotOffline,
              ]}
            />
            <Text style={styles.statusTitle}>
              {isLoading
                ? 'Comprobando conexión...'
                : healthData
                ? 'Backend Conectado'
                : 'Backend Desconectado'}
            </Text>
            {healthData && (
              <View style={styles.latencyBadge}>
                <Text style={styles.latencyText}>{healthData.latencyMs} ms</Text>
              </View>
            )}
          </View>

          {healthData ? (
            <View style={styles.detailsContainer}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Servicio:</Text>
                <Text style={styles.detailValue}>{healthData.service}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Versión:</Text>
                <Text style={styles.detailValue}>{healthData.version}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Proveedor LLM:</Text>
                <Text style={styles.detailValueHighlight}>{healthData.llm_provider}</Text>
              </View>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Modelo:</Text>
                <Text style={styles.detailValue}>{healthData.llm_model}</Text>
              </View>
            </View>
          ) : errorMsg ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMsg}</Text>
              <Text style={styles.errorHelp}>
                • Verifica que el backend de FastAPI esté corriendo.{'\n'}
                • Si pruebas en Android físico, asegúrate de estar en la misma red Wi-Fi y que el Firewall de Windows no bloquee el puerto {DEFAULT_PORT}.
              </Text>
            </View>
          ) : (
            <Text style={styles.statusSubtitle}>Esperando prueba de conexión...</Text>
          )}
        </View>

        {/* Configuration Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuración del Servidor</Text>
          <Text style={styles.inputLabel}>URL del Backend (FastAPI):</Text>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={backendUrl}
              onChangeText={setBackendUrl}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="http://192.168.1.xxx:8000"
              placeholderTextColor="#64748b"
            />
          </View>

          {/* Preset Buttons */}
          <Text style={styles.presetLabel}>Accesos rápidos de IP:</Text>
          <View style={styles.presetsRow}>
            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => {
                const url = `http://${DEFAULT_LAN_IP}:${DEFAULT_PORT}`;
                setBackendUrl(url);
                testConnection(url);
              }}
            >
              <Text style={styles.presetBtnText}>Wi-Fi Local ({DEFAULT_LAN_IP})</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => {
                const url = `http://10.0.2.2:${DEFAULT_PORT}`;
                setBackendUrl(url);
                testConnection(url);
              }}
            >
              <Text style={styles.presetBtnText}>Emulador Android (10.0.2.2)</Text>
            </TouchableOpacity>
          </View>

          {/* Action Button */}
          <TouchableOpacity
            style={[styles.primaryButton, isLoading && styles.buttonDisabled]}
            onPress={() => testConnection()}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.primaryButtonText}>Probar Conexión Ahora</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Logs Console */}
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
    marginBottom: 20,
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
    fontSize: 26,
    fontWeight: '800',
  },
  headerDescription: {
    color: '#94a3b8',
    fontSize: 14,
    marginTop: 4,
  },
  card: {
    borderRadius: 16,
    padding: 18,
    marginBottom: 24,
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
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
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
    fontSize: 17,
    fontWeight: '700',
    flex: 1,
  },
  latencyBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#10b981',
  },
  latencyText: {
    color: '#34d399',
    fontSize: 12,
    fontWeight: '600',
  },
  statusSubtitle: {
    color: '#94a3b8',
    fontSize: 13,
    marginTop: 8,
  },
  detailsContainer: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
  },
  detailLabel: {
    color: '#94a3b8',
    fontSize: 13,
  },
  detailValue: {
    color: '#f1f5f9',
    fontSize: 13,
    fontWeight: '500',
  },
  detailValueHighlight: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  errorBox: {
    marginTop: 12,
  },
  errorText: {
    color: '#fb7185',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
  },
  errorHelp: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 18,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: '#f8fafc',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  inputLabel: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 6,
  },
  inputContainer: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  input: {
    color: '#f8fafc',
    height: 44,
    fontSize: 14,
  },
  presetLabel: {
    color: '#94a3b8',
    fontSize: 12,
    marginBottom: 8,
  },
  presetsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
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
    fontSize: 12,
    fontWeight: '500',
  },
  primaryButton: {
    backgroundColor: '#0284c7',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#0284c7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
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
    minHeight: 120,
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
