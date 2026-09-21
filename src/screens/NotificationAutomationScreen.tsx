import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  sendBankWebhook,
  getRecentWebhookTransactions,
  WebhookRecentTransaction,
  BankWebhookResponse,
} from '../services/api';

interface NotificationAutomationScreenProps {
  backendUrl: string;
  onBackToAssistant: () => void;
  onOpenDiagnostics?: () => void;
}

interface NotificationPreset {
  id: string;
  bank: string;
  badgeColor: string;
  content: string;
}

const PRESETS: NotificationPreset[] = [
  {
    id: 'bancolombia_compra',
    bank: 'Bancolombia',
    badgeColor: '#fdba74',
    content: 'Bancolombia le informa compra por $45.000 en Supermercado Metro con su tarjeta de credito terminada en 4321',
  },
  {
    id: 'nequi_transferencia',
    bank: 'Nequi',
    badgeColor: '#f43f5e',
    content: '¡Te pasaron plata! Transferencia recibida por $120.000 de Pedro Perez. Tu nuevo saldo disponible es $350.000',
  },
  {
    id: 'nu_compra',
    bank: 'Nu Colombia',
    badgeColor: '#a855f7',
    content: 'Compra aprobada por $89.900 en Restaurante El Corral con tu tarjeta Nu debito',
  },
  {
    id: 'davivienda_cargo',
    bank: 'Davivienda',
    badgeColor: '#ef4444',
    content: 'Davivienda informa retiro o cargo por $24.500 en Farmacia Drogas La Rebaja el 21/09 con TD 5678',
  },
];

export default function NotificationAutomationScreen({
  backendUrl,
  onBackToAssistant,
  onOpenDiagnostics,
}: NotificationAutomationScreenProps) {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('bancolombia_compra');
  const [notificationContent, setNotificationContent] = useState<string>(PRESETS[0].content);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<BankWebhookResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Monitor de transacciones recientes
  const [transactions, setTransactions] = useState<WebhookRecentTransaction[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Tab activo: 'simulator' | 'guide' | 'history'
  const [activeTab, setActiveTab] = useState<'simulator' | 'history' | 'guide'>('simulator');

  const fetchRecentTransactions = useCallback(async () => {
    setIsLoadingHistory(true);
    setHistoryError(null);
    try {
      const data = await getRecentWebhookTransactions(backendUrl, 10);
      setTransactions(data.transactions || []);
    } catch (err: any) {
      setHistoryError(err.message || 'Error cargando transacciones');
    } finally {
      setIsLoadingHistory(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    fetchRecentTransactions();
  }, [fetchRecentTransactions]);

  const handleSelectPreset = (preset: NotificationPreset) => {
    setSelectedPresetId(preset.id);
    setNotificationContent(preset.content);
    setErrorMessage(null);
  };

  const handleSendWebhook = async () => {
    if (!notificationContent.trim()) {
      setErrorMessage('Por favor ingresa o selecciona el texto de una notificación');
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);
    setLastResult(null);

    try {
      const response = await sendBankWebhook(backendUrl, {
        source: 'android_notification_listener',
        content: notificationContent.trim(),
      });
      setLastResult(response);
      // Refrescar historial
      fetchRecentTransactions();
    } catch (err: any) {
      setErrorMessage(err.message || 'Error enviando webhook');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = 'COP') => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: currency || 'COP',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={onBackToAssistant}
            activeOpacity={0.7}
          >
            <Text style={styles.backButtonText}>← Volver</Text>
          </TouchableOpacity>
          <View style={styles.headerTitleContainer}>
            <Text style={styles.headerTitle}>Automatización Bancaria</Text>
            <Text style={styles.headerSubtitle}>Ingesta Android · POST /webhooks/bank</Text>
          </View>
          {onOpenDiagnostics && (
            <TouchableOpacity
              style={styles.diagButton}
              onPress={onOpenDiagnostics}
              activeOpacity={0.7}
            >
              <Text style={styles.diagButtonText}>Red</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Diagrama de Flujo Resumido */}
        <View style={styles.flowBanner}>
          <Text style={styles.flowStep}>Banco</Text>
          <Text style={styles.flowArrow}>→</Text>
          <Text style={styles.flowStep}>Notif Android</Text>
          <Text style={styles.flowArrow}>→</Text>
          <Text style={styles.flowStepHighlight}>Listener/Macro</Text>
          <Text style={styles.flowArrow}>→</Text>
          <Text style={styles.flowStep}>Webhook</Text>
          <Text style={styles.flowArrow}>→</Text>
          <Text style={styles.flowStep}>LLM</Text>
          <Text style={styles.flowArrow}>→</Text>
          <Text style={styles.flowStep}>PostgreSQL</Text>
        </View>

        {/* Selector de Pestañas */}
        <View style={styles.tabsContainer}>
          <TouchableOpacity
            style={[styles.tabButton, activeTab === 'simulator' && styles.tabButtonActive]}
            onPress={() => setActiveTab('simulator')}
            activeOpacity={0.7}
          >
            <Text style={[styles.tabText, activeTab === 'simulator' && styles.tabTextActive]}>
              Simulador
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, activeTab === 'history' && styles.tabButtonActive]}
            onPress={() => setActiveTab('history')}
            activeOpacity={0.7}
          >
            <Text style={[styles.tabText, activeTab === 'history' && styles.tabTextActive]}>
              Historial ({transactions.length})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, activeTab === 'guide' && styles.tabButtonActive]}
            onPress={() => setActiveTab('guide')}
            activeOpacity={0.7}
          >
            <Text style={[styles.tabText, activeTab === 'guide' && styles.tabTextActive]}>
              Guía MacroDroid
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView
          style={styles.scrollArea}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* TAB 1: SIMULADOR DE NOTIFICACIONES */}
          {activeTab === 'simulator' && (
            <View style={styles.tabContent}>
              <Text style={styles.sectionTitle}>1. Presets de Notificaciones Bancarias</Text>
              <Text style={styles.sectionHelp}>
                Selecciona una plantilla o escribe el contenido de cualquier alerta SMS o notificación bancaria:
              </Text>

              <View style={styles.presetsGrid}>
                {PRESETS.map((preset) => {
                  const isSelected = selectedPresetId === preset.id;
                  return (
                    <TouchableOpacity
                      key={preset.id}
                      style={[styles.presetCard, isSelected && styles.presetCardActive]}
                      onPress={() => handleSelectPreset(preset)}
                      activeOpacity={0.7}
                    >
                      <View style={styles.presetHeader}>
                        <View style={[styles.badge, { backgroundColor: preset.badgeColor }]}>
                          <Text style={styles.badgeText}>{preset.bank}</Text>
                        </View>
                        {isSelected && <Text style={styles.checkIcon}>✓</Text>}
                      </View>
                      <Text style={styles.presetSnippet} numberOfLines={2}>
                        {preset.content}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <Text style={styles.sectionTitle}>2. Texto de la Notificación Entrante</Text>
              <TextInput
                style={styles.textInput}
                multiline
                numberOfLines={4}
                value={notificationContent}
                onChangeText={setNotificationContent}
                placeholder="Escribe la notificación aquí..."
                placeholderTextColor="#64748b"
              />

              <TouchableOpacity
                style={[styles.sendButton, isProcessing && styles.sendButtonDisabled]}
                onPress={handleSendWebhook}
                disabled={isProcessing}
                activeOpacity={0.8}
              >
                {isProcessing ? (
                  <View style={styles.loadingRow}>
                    <ActivityIndicator color="#0f172a" size="small" />
                    <Text style={styles.sendButtonText}>Extrayendo con LLM y Guardando...</Text>
                  </View>
                ) : (
                  <Text style={styles.sendButtonText}>Disparar Webhook Bancario</Text>
                )}
              </TouchableOpacity>

              {errorMessage && (
                <View style={styles.errorBox}>
                  <Text style={styles.errorBoxTitle}>Error en Webhook</Text>
                  <Text style={styles.errorBoxText}>{errorMessage}</Text>
                </View>
              )}

              {lastResult && (
                <View style={styles.resultBox}>
                  <View style={styles.resultHeader}>
                    <Text style={styles.resultBadge}>Procesado Exitosamente</Text>
                    <Text style={styles.resultTxId}>ID: {lastResult.transaction_id.slice(0, 8)}...</Text>
                  </View>
                  <Text style={styles.resultMessage}>{lastResult.message}</Text>

                  <View style={styles.resultGrid}>
                    <View style={styles.resultItem}>
                      <Text style={styles.resultLabel}>Monto</Text>
                      <Text style={styles.resultValueHighlight}>
                        {formatCurrency(lastResult.extracted.amount, lastResult.extracted.currency)}
                      </Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Text style={styles.resultLabel}>Comercio</Text>
                      <Text style={styles.resultValue}>{lastResult.extracted.merchant}</Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Text style={styles.resultLabel}>Tipo</Text>
                      <Text style={styles.resultValue}>{lastResult.extracted.type.toUpperCase()}</Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Text style={styles.resultLabel}>Categoría</Text>
                      <Text style={styles.resultValue}>{lastResult.extracted.category}</Text>
                    </View>
                    <View style={styles.resultItem}>
                      <Text style={styles.resultLabel}>Medio de Pago</Text>
                      <Text style={styles.resultValue}>{lastResult.extracted.payment_method}</Text>
                    </View>
                  </View>
                </View>
              )}
            </View>
          )}

          {/* TAB 2: HISTORIAL DE TRANSACCIONES DEL WEBHOOK */}
          {activeTab === 'history' && (
            <View style={styles.tabContent}>
              <View style={styles.historyTopBar}>
                <Text style={styles.sectionTitle}>Transacciones Capturadas</Text>
                <TouchableOpacity
                  style={styles.refreshButton}
                  onPress={fetchRecentTransactions}
                  disabled={isLoadingHistory}
                >
                  <Text style={styles.refreshButtonText}>
                    {isLoadingHistory ? 'Cargando...' : 'Actualizar'}
                  </Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.sectionHelp}>
                Listado en vivo de transacciones guardadas en PostgreSQL con origen `webhook_bank`:
              </Text>

              {historyError && (
                <View style={styles.errorBox}>
                  <Text style={styles.errorBoxText}>{historyError}</Text>
                </View>
              )}

              {transactions.length === 0 && !isLoadingHistory ? (
                <View style={styles.emptyBox}>
                  <Text style={styles.emptyText}>No hay transacciones registradas por webhook aún.</Text>
                  <Text style={styles.emptySubtext}>
                    Envía una notificación desde la pestaña Simulador para verla aquí.
                  </Text>
                </View>
              ) : (
                transactions.map((tx) => (
                  <View key={tx.id} style={styles.txCard}>
                    <View style={styles.txCardHeader}>
                      <View>
                        <Text style={styles.txMerchant}>{tx.merchant || 'Comercio General'}</Text>
                        <Text style={styles.txCategory}>
                          {tx.category.toUpperCase()} · {tx.source}
                        </Text>
                      </View>
                      <Text
                        style={[
                          styles.txAmount,
                          tx.type === 'income' ? styles.txAmountIncome : styles.txAmountExpense,
                        ]}
                      >
                        {tx.type === 'income' ? '+' : '-'}
                        {formatCurrency(tx.amount, tx.currency)}
                      </Text>
                    </View>
                    {tx.description ? (
                      <Text style={styles.txDescription}>{tx.description}</Text>
                    ) : null}
                    <Text style={styles.txDate}>
                      {tx.transaction_date ? new Date(tx.transaction_date).toLocaleString('es-CO') : 'Reciente'}
                    </Text>
                  </View>
                ))
              )}
            </View>
          )}

          {/* TAB 3: GUÍA DE CONFIGURACIÓN ANDROID (MACRODROID / TASKER) */}
          {activeTab === 'guide' && (
            <View style={styles.tabContent}>
              <Text style={styles.sectionTitle}>Configuración Android con MacroDroid</Text>
              <Text style={styles.sectionHelp}>
                Sigue estos pasos en tu teléfono físico Android para capturar notificaciones bancarias automáticamente en segundo plano:
              </Text>

              <View style={styles.guideStep}>
                <Text style={styles.stepNumber}>Paso 1</Text>
                <Text style={styles.stepText}>
                  Instala <Text style={styles.bold}>MacroDroid</Text> (gratis) desde Google Play Store y concédele el permiso de <Text style={styles.bold}>Acceso a Notificaciones</Text> (NotificationListenerService).
                </Text>
              </View>

              <View style={styles.guideStep}>
                <Text style={styles.stepNumber}>Paso 2</Text>
                <Text style={styles.stepText}>
                  Crea una nueva Macro. En <Text style={styles.bold}>Disparadores (Triggers)</Text>, selecciona:{'\n'}
                  • <Text style={styles.italic}>Notificación → Notificación recibida</Text>{'\n'}
                  • Selecciona las apps de tus bancos (ej. Bancolombia, Nequi, Nu) o marca <Text style={styles.italic}>Cualquier aplicación</Text> con filtro de contenido: <Text style={styles.bold}>Compra, Transferencia, Cargo</Text>.
                </Text>
              </View>

              <View style={styles.guideStep}>
                <Text style={styles.stepNumber}>Paso 3</Text>
                <Text style={styles.stepText}>
                  En <Text style={styles.bold}>Acciones (Actions)</Text>, selecciona:{'\n'}
                  • <Text style={styles.italic}>Conectividad → Solicitud HTTP (HTTP Request)</Text>{'\n'}
                  • Método: <Text style={styles.bold}>POST</Text>{'\n'}
                  • URL: <Text style={styles.codeText}>{backendUrl}/webhooks/bank</Text>{'\n'}
                  • Content-Type: <Text style={styles.codeText}>application/json</Text>{'\n'}
                  • Cuerpo de la solicitud:{'\n'}
                  <Text style={styles.codeBlock}>
                    {`{\n  "source": "macrodroid_android",\n  "content": "[notif_text]"\n}`}
                  </Text>
                </Text>
              </View>

              <View style={styles.guideStep}>
                <Text style={styles.stepNumber}>Paso 4</Text>
                <Text style={styles.stepText}>
                  Guarda la Macro. A partir de ese momento, cada vez que llegue una notificación de tu banco o SMS, MacroDroid ejecutará el webhook hacia tu backend en FastAPI por Tailscale/LAN, el LLM extraerá los datos estructurados y se guardará en PostgreSQL.
                </Text>
              </View>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    backgroundColor: '#0f172a',
  },
  backButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#1e293b',
  },
  backButtonText: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '600',
  },
  headerTitleContainer: {
    alignItems: 'center',
  },
  headerTitle: {
    color: '#f8fafc',
    fontSize: 16,
    fontWeight: '700',
  },
  headerSubtitle: {
    color: '#64748b',
    fontSize: 11,
    marginTop: 2,
  },
  diagButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#334155',
  },
  diagButtonText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  flowBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111827',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937',
  },
  flowStep: {
    color: '#9ca3af',
    fontSize: 10,
    fontWeight: '500',
  },
  flowStepHighlight: {
    color: '#38bdf8',
    fontSize: 10,
    fontWeight: '700',
  },
  flowArrow: {
    color: '#4b5563',
    fontSize: 9,
    marginHorizontal: 4,
  },
  tabsContainer: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    gap: 8,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#1e293b',
  },
  tabButtonActive: {
    backgroundColor: '#0284c7',
  },
  tabText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  tabContent: {
    gap: 12,
  },
  sectionTitle: {
    color: '#e2e8f0',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 6,
  },
  sectionHelp: {
    color: '#94a3b8',
    fontSize: 12,
    lineHeight: 18,
  },
  presetsGrid: {
    gap: 8,
  },
  presetCard: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  presetCardActive: {
    borderColor: '#38bdf8',
    backgroundColor: '#172554',
  },
  presetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  badgeText: {
    color: '#0f172a',
    fontSize: 10,
    fontWeight: '700',
  },
  checkIcon: {
    color: '#38bdf8',
    fontSize: 14,
    fontWeight: '700',
  },
  presetSnippet: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 16,
  },
  textInput: {
    backgroundColor: '#1e293b',
    borderColor: '#334155',
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    color: '#f8fafc',
    fontSize: 13,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  sendButton: {
    backgroundColor: '#38bdf8',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
  },
  sendButtonDisabled: {
    backgroundColor: '#64748b',
    opacity: 0.6,
  },
  sendButtonText: {
    color: '#0f172a',
    fontSize: 14,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  errorBox: {
    backgroundColor: '#450a0a',
    borderColor: '#991b1b',
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginTop: 8,
  },
  errorBoxTitle: {
    color: '#fca5a5',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },
  errorBoxText: {
    color: '#fecaca',
    fontSize: 12,
  },
  resultBox: {
    backgroundColor: '#064e3b',
    borderColor: '#059669',
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    marginTop: 8,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  resultBadge: {
    color: '#6ee7b7',
    fontSize: 11,
    fontWeight: '700',
  },
  resultTxId: {
    color: '#a7f3d0',
    fontSize: 11,
  },
  resultMessage: {
    color: '#d1fae5',
    fontSize: 12,
    marginBottom: 10,
  },
  resultGrid: {
    backgroundColor: '#022c22',
    borderRadius: 8,
    padding: 10,
    gap: 6,
  },
  resultItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  resultLabel: {
    color: '#6ee7b7',
    fontSize: 12,
  },
  resultValue: {
    color: '#f0fdf4',
    fontSize: 12,
    fontWeight: '600',
  },
  resultValueHighlight: {
    color: '#34d399',
    fontSize: 14,
    fontWeight: '700',
  },
  historyTopBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  refreshButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#1e293b',
  },
  refreshButtonText: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '600',
  },
  emptyBox: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyText: {
    color: '#64748b',
    fontSize: 14,
    fontWeight: '600',
  },
  emptySubtext: {
    color: '#475569',
    fontSize: 12,
    marginTop: 4,
    textAlign: 'center',
  },
  txCard: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 4,
  },
  txCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  txMerchant: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '700',
  },
  txCategory: {
    color: '#94a3b8',
    fontSize: 10,
    marginTop: 2,
  },
  txAmount: {
    fontSize: 14,
    fontWeight: '700',
  },
  txAmountExpense: {
    color: '#f87171',
  },
  txAmountIncome: {
    color: '#4ade80',
  },
  txDescription: {
    color: '#cbd5e1',
    fontSize: 11,
    marginTop: 2,
  },
  txDate: {
    color: '#64748b',
    fontSize: 10,
    marginTop: 2,
  },
  guideStep: {
    backgroundColor: '#1e293b',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  stepNumber: {
    color: '#38bdf8',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },
  stepText: {
    color: '#cbd5e1',
    fontSize: 12,
    lineHeight: 18,
  },
  bold: {
    fontWeight: '700',
    color: '#f8fafc',
  },
  italic: {
    fontStyle: 'italic',
    color: '#38bdf8',
  },
  codeText: {
    color: '#fbbf24',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  codeBlock: {
    backgroundColor: '#0f172a',
    padding: 8,
    borderRadius: 6,
    color: '#a5f3fc',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 11,
    marginTop: 4,
  },
});
