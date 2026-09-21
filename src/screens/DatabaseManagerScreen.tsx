import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  FlatList,
  Modal,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DEFAULT_BACKEND_URL } from '../config';
import {
  fetchDatabaseSummary,
  fetchTableRecords,
  createTableRecord,
  updateTableRecord,
  deleteTableRecord,
  DatabaseSummaryResponse,
} from '../services/api';

interface DatabaseManagerScreenProps {
  backendUrl?: string;
  onBackToAssistant: () => void;
  onOpenDiagnostics?: () => void;
}

type TabType = 'tasks' | 'reminders' | 'transactions' | 'financial_accounts' | 'emails' | 'saving_goals';

interface TabConfig {
  key: TabType;
  title: string;
  icon: string;
  countKey: string;
}

const TABS: TabConfig[] = [
  { key: 'tasks', title: 'Tareas', icon: '📋', countKey: 'tasks' },
  { key: 'reminders', title: 'Recordatorios', icon: '⏰', countKey: 'reminders' },
  { key: 'transactions', title: 'Transacciones', icon: '💰', countKey: 'transactions' },
  { key: 'financial_accounts', title: 'Cuentas', icon: '🏦', countKey: 'financial_accounts' },
  { key: 'emails', title: 'Correos', icon: '✉️', countKey: 'emails' },
  { key: 'saving_goals', title: 'Metas', icon: '🎯', countKey: 'saving_goals' },
];

function formatCOP(amount: number | string | undefined): string {
  if (amount === undefined || amount === null || isNaN(Number(amount))) return '$0 COP';
  const num = Math.round(Number(amount));
  return `$${num.toLocaleString('es-CO')} COP`;
}

export default function DatabaseManagerScreen({
  backendUrl = DEFAULT_BACKEND_URL,
  onBackToAssistant,
  onOpenDiagnostics,
}: DatabaseManagerScreenProps) {
  const [activeTab, setActiveTab] = useState<TabType>('tasks');
  const [summary, setSummary] = useState<DatabaseSummaryResponse | null>(null);
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal State for Manual Creation
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Form Fields State
  const [formTitle, setFormTitle] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formCategory, setFormCategory] = useState<string>('general');
  const [formPriority, setFormPriority] = useState<string>('medium');
  const [formDueDate, setFormDueDate] = useState<string>('');
  
  // Transaction fields
  const [formTxType, setFormTxType] = useState<'expense' | 'income'>('expense');
  const [formAmount, setFormAmount] = useState<string>('');
  const [formMerchant, setFormMerchant] = useState<string>('');

  // Account / Goal fields
  const [formInstitution, setFormInstitution] = useState<string>('Bancolombia');
  const [formAccountType, setFormAccountType] = useState<string>('savings');
  const [formTargetAmount, setFormTargetAmount] = useState<string>('');
  const [formCurrentAmount, setFormCurrentAmount] = useState<string>('0');
  const [formDeadline, setFormDeadline] = useState<string>('');

  // Load summary counts
  const loadSummary = useCallback(async () => {
    try {
      const sum = await fetchDatabaseSummary(backendUrl);
      setSummary(sum);
    } catch (err: any) {
      console.warn('[DB Manager] Could not load summary:', err);
    }
  }, [backendUrl]);

  // Load records for active tab
  const loadRecords = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetchTableRecords(backendUrl, activeTab);
      setRecords(res.data || []);
      await loadSummary();
    } catch (err: any) {
      setErrorMessage(err.message || 'Error cargando datos de la base de datos');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [backendUrl, activeTab, loadSummary]);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadRecords();
  };

  const resetForm = () => {
    setFormTitle('');
    setFormDescription('');
    setFormCategory('general');
    setFormPriority('medium');
    setFormDueDate('');
    setFormTxType('expense');
    setFormAmount('');
    setFormMerchant('');
    setFormInstitution('Bancolombia');
    setFormAccountType('savings');
    setFormTargetAmount('');
    setFormCurrentAmount('0');
    setFormDeadline('');
  };

  // Submit new manual record
  const handleCreateRecord = async () => {
    if (activeTab === 'tasks' || activeTab === 'reminders') {
      if (!formTitle.trim()) {
        Alert.alert('Campo requerido', 'Por favor ingresa un título para la tarea/recordatorio.');
        return;
      }
    } else if (activeTab === 'transactions') {
      if (!formDescription.trim() || !formAmount.trim()) {
        Alert.alert('Campos requeridos', 'Ingresa la descripción y el monto de la transacción.');
        return;
      }
    } else if (activeTab === 'financial_accounts') {
      if (!formTitle.trim()) {
        Alert.alert('Campo requerido', 'Ingresa el nombre de la cuenta (ej. Ahorros Principal).');
        return;
      }
    } else if (activeTab === 'saving_goals') {
      if (!formTitle.trim() || !formTargetAmount.trim()) {
        Alert.alert('Campos requeridos', 'Ingresa el nombre y monto objetivo de la meta.');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      let payload: Record<string, any> = {};

      if (activeTab === 'tasks') {
        payload = {
          title: formTitle.trim(),
          description: formDescription.trim() || undefined,
          priority: formPriority,
          category: formCategory.trim() || 'general',
          due_date: formDueDate.trim() || undefined,
          status: 'pending',
        };
      } else if (activeTab === 'reminders') {
        payload = {
          title: formTitle.trim(),
          description: formDescription.trim() || undefined,
          remind_at: formDueDate.trim() || 'Hoy, en 1 hora',
          category: 'reminder',
          status: 'pending',
          priority: formPriority,
        };
      } else if (activeTab === 'transactions') {
        payload = {
          type: formTxType,
          amount: parseFloat(formAmount) || 0,
          currency: 'COP',
          category: formCategory.trim() || 'general',
          description: formDescription.trim(),
          merchant: formMerchant.trim() || undefined,
          source: 'manual',
          status: 'posted',
        };
      } else if (activeTab === 'financial_accounts') {
        payload = {
          account_name: formTitle.trim(),
          institution: formInstitution.trim() || 'Bancolombia',
          account_type: formAccountType,
          balance: parseFloat(formAmount) || 0,
          currency: 'COP',
          status: 'active',
        };
      } else if (activeTab === 'saving_goals') {
        payload = {
          goal_name: formTitle.trim(),
          target_amount: parseFloat(formTargetAmount) || 1000000,
          current_amount: parseFloat(formCurrentAmount) || 0,
          currency: 'COP',
          deadline: formDeadline.trim() || undefined,
          status: 'in_progress',
        };
      }

      await createTableRecord(backendUrl, activeTab, payload);
      setIsModalVisible(false);
      resetForm();
      Alert.alert('Éxito', 'Registro guardado exitosamente en la base de datos.');
      loadRecords();
    } catch (err: any) {
      Alert.alert('Error al guardar', err.message || 'No se pudo guardar el registro');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle complete for task or reminder
  const handleToggleTaskStatus = async (item: any) => {
    const isCompleted = item.status === 'completed';
    const newStatus = isCompleted ? 'pending' : 'completed';
    try {
      await updateTableRecord(backendUrl, activeTab, item.id, { status: newStatus });
      // Update local state smoothly
      setRecords((prev) =>
        prev.map((r) => (r.id === item.id ? { ...r, status: newStatus } : r))
      );
    } catch (err: any) {
      Alert.alert('Error', `No se pudo actualizar el estado: ${err.message}`);
    }
  };

  // Delete record
  const handleDeleteRecord = (recordId: string, title?: string) => {
    Alert.alert(
      'Confirmar eliminación',
      `¿Deseas eliminar definitivamente este registro "${title || recordId}" de la base de datos?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteTableRecord(backendUrl, activeTab, recordId);
              setRecords((prev) => prev.filter((r) => r.id !== recordId));
              loadSummary();
            } catch (err: any) {
              Alert.alert('Error', `No se pudo eliminar: ${err.message}`);
            }
          },
        },
      ]
    );
  };

  // Render individual item card
  const renderItem = ({ item }: { item: any }) => {
    if (activeTab === 'tasks' || activeTab === 'reminders') {
      const isCompleted = item.status === 'completed';
      return (
        <View style={[styles.card, isCompleted && styles.cardCompleted]}>
          <View style={styles.cardHeader}>
            <TouchableOpacity
              style={[styles.statusCheckbox, isCompleted && styles.checkboxCompleted]}
              onPress={() => handleToggleTaskStatus(item)}
              activeOpacity={0.7}
            >
              <Text style={styles.checkboxText}>{isCompleted ? '✓' : '○'}</Text>
            </TouchableOpacity>
            <View style={styles.cardHeaderInfo}>
              <Text style={[styles.cardTitle, isCompleted && styles.textCrossed]}>
                {item.title}
              </Text>
              <View style={styles.badgeRow}>
                <View style={[styles.pill, styles.priorityPill]}>
                  <Text style={styles.priorityText}>{item.priority || 'media'}</Text>
                </View>
                <View style={[styles.pill, styles.categoryPill]}>
                  <Text style={styles.categoryText}>{item.category || 'general'}</Text>
                </View>
                {item.due_date && (
                  <View style={[styles.pill, styles.duePill]}>
                    <Text style={styles.dueText}>📅 {item.due_date}</Text>
                  </View>
                )}
              </View>
            </View>
            <TouchableOpacity
              style={styles.deleteBtn}
              onPress={() => handleDeleteRecord(item.id, item.title)}
              activeOpacity={0.7}
            >
              <Text style={styles.deleteBtnText}>🗑️</Text>
            </TouchableOpacity>
          </View>
          {item.description ? (
            <Text style={styles.cardDesc}>{item.description}</Text>
          ) : null}
        </View>
      );
    }

    if (activeTab === 'transactions') {
      const isIncome = item.type === 'income';
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={[styles.txIconPill, isIncome ? styles.txIncome : styles.txExpense]}>
              <Text style={styles.txIconText}>{isIncome ? '📈' : '📉'}</Text>
            </View>
            <View style={styles.cardHeaderInfo}>
              <Text style={styles.cardTitle}>{item.description}</Text>
              <Text style={[styles.txAmount, isIncome ? styles.incomeText : styles.expenseText]}>
                {isIncome ? '+' : '-'}{formatCOP(item.amount)}
              </Text>
              <View style={styles.badgeRow}>
                <View style={[styles.pill, styles.categoryPill]}>
                  <Text style={styles.categoryText}>{item.category}</Text>
                </View>
                {item.merchant ? (
                  <View style={[styles.pill, styles.merchantPill]}>
                    <Text style={styles.merchantText}>🏪 {item.merchant}</Text>
                  </View>
                ) : null}
                <View style={[styles.pill, styles.sourcePill]}>
                  <Text style={styles.sourceText}>{item.source || 'manual'}</Text>
                </View>
              </View>
            </View>
            <TouchableOpacity
              style={styles.deleteBtn}
              onPress={() => handleDeleteRecord(item.id, item.description)}
              activeOpacity={0.7}
            >
              <Text style={styles.deleteBtnText}>🗑️</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    if (activeTab === 'financial_accounts') {
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={[styles.txIconPill, styles.accountPillBg]}>
              <Text style={styles.txIconText}>🏦</Text>
            </View>
            <View style={styles.cardHeaderInfo}>
              <Text style={styles.cardTitle}>{item.account_name}</Text>
              <Text style={styles.accountInstitution}>{item.institution} • {item.account_type}</Text>
              <Text style={styles.accountBalanceText}>{formatCOP(item.balance)}</Text>
            </View>
          </View>
        </View>
      );
    }

    if (activeTab === 'emails') {
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={[styles.txIconPill, styles.emailPillBg]}>
              <Text style={styles.txIconText}>✉️</Text>
            </View>
            <View style={styles.cardHeaderInfo}>
              <Text style={styles.cardTitle}>{item.subject}</Text>
              <Text style={styles.emailSender}>De: {item.sender}</Text>
              {item.snippet ? <Text style={styles.cardDesc} numberOfLines={2}>{item.snippet}</Text> : null}
            </View>
            <View style={[styles.pill, item.status === 'unread' ? styles.unreadPill : styles.readPill]}>
              <Text style={styles.statusLabel}>{item.status}</Text>
            </View>
          </View>
        </View>
      );
    }

    if (activeTab === 'saving_goals') {
      const target = Number(item.target_amount) || 1;
      const current = Number(item.current_amount) || 0;
      const percent = Math.min(100, Math.round((current / target) * 100));

      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View style={[styles.txIconPill, styles.goalPillBg]}>
              <Text style={styles.txIconText}>🎯</Text>
            </View>
            <View style={styles.cardHeaderInfo}>
              <Text style={styles.cardTitle}>{item.goal_name}</Text>
              <Text style={styles.goalMetaText}>
                {formatCOP(current)} de {formatCOP(target)} ({percent}%)
              </Text>
              {/* Progress Bar */}
              <View style={styles.progressBarTrack}>
                <View style={[styles.progressBarFill, { width: `${percent}%` }]} />
              </View>
              {item.deadline && (
                <Text style={styles.goalDeadlineText}>Meta para: {item.deadline}</Text>
              )}
            </View>
          </View>
        </View>
      );
    }

    return null;
  };

  const activeTabConfig = TABS.find((t) => t.key === activeTab);

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Top Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backBtn} onPress={onBackToAssistant} activeOpacity={0.7}>
          <Text style={styles.backBtnText}>← Volver</Text>
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={styles.headerTitle}>Gestor de Datos & DB</Text>
          <Text style={styles.headerSub} numberOfLines={1}>{backendUrl}</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={handleRefresh} activeOpacity={0.7}>
          <Text style={styles.refreshBtnText}>🔄</Text>
        </TouchableOpacity>
      </View>

      {/* Navigation Tabs Bar */}
      <View style={styles.tabBarContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabBarContent}>
          {TABS.map((tab) => {
            const isSelected = activeTab === tab.key;
            const count = summary?.counts?.[tab.countKey] ?? summary?.counts?.[tab.key] ?? 0;
            return (
              <TouchableOpacity
                key={tab.key}
                style={[styles.tabButton, isSelected && styles.tabButtonActive]}
                onPress={() => setActiveTab(tab.key)}
                activeOpacity={0.8}
              >
                <Text style={styles.tabIcon}>{tab.icon}</Text>
                <Text style={[styles.tabTitle, isSelected && styles.tabTitleActive]}>
                  {tab.title}
                </Text>
                <View style={[styles.tabBadge, isSelected && styles.tabBadgeActive]}>
                  <Text style={[styles.tabBadgeText, isSelected && styles.tabBadgeTextActive]}>
                    {count}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Error Notice */}
      {errorMessage && (
        <View style={styles.errorNotice}>
          <Text style={styles.errorNoticeText}>⚠️ {errorMessage}</Text>
        </View>
      )}

      {/* Main Content Area */}
      <View style={styles.contentArea}>
        {loading ? (
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color="#6366F1" />
            <Text style={styles.loadingText}>Cargando {activeTabConfig?.title}...</Text>
          </View>
        ) : (
          <FlatList
            data={records}
            keyExtractor={(item) => item.id || String(Math.random())}
            renderItem={renderItem}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#6366F1" />
            }
            ListEmptyComponent={
              <View style={styles.centerContainer}>
                <Text style={styles.emptyIcon}>{activeTabConfig?.icon}</Text>
                <Text style={styles.emptyTitle}>No hay registros en {activeTabConfig?.title}</Text>
                <Text style={styles.emptySub}>Puedes agregar uno nuevo pulsando el botón inferior.</Text>
              </View>
            }
          />
        )}
      </View>

      {/* Bottom Floating Action Bar */}
      {activeTab !== 'emails' && (
        <View style={styles.bottomBar}>
          <TouchableOpacity
            style={styles.addBtn}
            onPress={() => {
              resetForm();
              setIsModalVisible(true);
            }}
            activeOpacity={0.85}
          >
            <Text style={styles.addBtnText}>+ Agregar {activeTabConfig?.title.slice(0, -1)}</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Modal: Formulario CRUD de Creación */}
      <Modal visible={isModalVisible} animationType="slide" transparent={true}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.modalOverlay}
        >
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Nuevo: {activeTabConfig?.title}</Text>
              <TouchableOpacity onPress={() => setIsModalVisible(false)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalScroll}>
              {/* Form fields for Tasks & Reminders */}
              {(activeTab === 'tasks' || activeTab === 'reminders') && (
                <>
                  <Text style={styles.inputLabel}>Título *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Comprar repuestos del motor"
                    placeholderTextColor="#64748B"
                    value={formTitle}
                    onChangeText={setFormTitle}
                  />

                  <Text style={styles.inputLabel}>Descripción (opcional)</Text>
                  <TextInput
                    style={[styles.textInput, styles.textArea]}
                    placeholder="Detalles adicionales..."
                    placeholderTextColor="#64748B"
                    multiline
                    value={formDescription}
                    onChangeText={setFormDescription}
                  />

                  <Text style={styles.inputLabel}>Fecha / Hora Límite</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Mañana, 9:00 a.m."
                    placeholderTextColor="#64748B"
                    value={formDueDate}
                    onChangeText={setFormDueDate}
                  />

                  <Text style={styles.inputLabel}>Prioridad</Text>
                  <View style={styles.selectorRow}>
                    {['low', 'medium', 'high', 'urgent'].map((p) => (
                      <TouchableOpacity
                        key={p}
                        style={[styles.selectorBtn, formPriority === p && styles.selectorBtnActive]}
                        onPress={() => setFormPriority(p)}
                      >
                        <Text style={[styles.selectorBtnText, formPriority === p && styles.selectorBtnTextActive]}>
                          {p}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </>
              )}

              {/* Form fields for Transactions */}
              {activeTab === 'transactions' && (
                <>
                  <Text style={styles.inputLabel}>Tipo de Transacción</Text>
                  <View style={styles.selectorRow}>
                    <TouchableOpacity
                      style={[styles.selectorBtn, formTxType === 'expense' && styles.selectorBtnActive]}
                      onPress={() => setFormTxType('expense')}
                    >
                      <Text style={[styles.selectorBtnText, formTxType === 'expense' && styles.selectorBtnTextActive]}>
                        📉 Gasto
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.selectorBtn, formTxType === 'income' && styles.selectorBtnActive]}
                      onPress={() => setFormTxType('income')}
                    >
                      <Text style={[styles.selectorBtnText, formTxType === 'income' && styles.selectorBtnTextActive]}>
                        📈 Ingreso
                      </Text>
                    </TouchableOpacity>
                  </View>

                  <Text style={styles.inputLabel}>Monto en COP ($) *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. 45000"
                    placeholderTextColor="#64748B"
                    keyboardType="numeric"
                    value={formAmount}
                    onChangeText={setFormAmount}
                  />

                  <Text style={styles.inputLabel}>Descripción del Gasto/Ingreso *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Almuerzo restaurante"
                    placeholderTextColor="#64748B"
                    value={formDescription}
                    onChangeText={setFormDescription}
                  />

                  <Text style={styles.inputLabel}>Comercio o Establecimiento</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Éxito, Juan Valdez, Uber"
                    placeholderTextColor="#64748B"
                    value={formMerchant}
                    onChangeText={setFormMerchant}
                  />

                  <Text style={styles.inputLabel}>Categoría</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="alimentacion, transporte, servicios..."
                    placeholderTextColor="#64748B"
                    value={formCategory}
                    onChangeText={setFormCategory}
                  />
                </>
              )}

              {/* Form fields for Financial Accounts */}
              {activeTab === 'financial_accounts' && (
                <>
                  <Text style={styles.inputLabel}>Nombre de la Cuenta *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Cuenta de Ahorros Principal"
                    placeholderTextColor="#64748B"
                    value={formTitle}
                    onChangeText={setFormTitle}
                  />

                  <Text style={styles.inputLabel}>Institución Financiera</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Bancolombia, Nequi, Davivienda"
                    placeholderTextColor="#64748B"
                    value={formInstitution}
                    onChangeText={setFormInstitution}
                  />

                  <Text style={styles.inputLabel}>Saldo Inicial en COP ($)</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. 1500000"
                    placeholderTextColor="#64748B"
                    keyboardType="numeric"
                    value={formAmount}
                    onChangeText={setFormAmount}
                  />
                </>
              )}

              {/* Form fields for Saving Goals */}
              {activeTab === 'saving_goals' && (
                <>
                  <Text style={styles.inputLabel}>Nombre de la Meta *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. Viaje a Cartagena"
                    placeholderTextColor="#64748B"
                    value={formTitle}
                    onChangeText={setFormTitle}
                  />

                  <Text style={styles.inputLabel}>Monto Objetivo en COP ($) *</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. 3000000"
                    placeholderTextColor="#64748B"
                    keyboardType="numeric"
                    value={formTargetAmount}
                    onChangeText={setFormTargetAmount}
                  />

                  <Text style={styles.inputLabel}>Monto Actual Ahorrado en COP ($)</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. 500000"
                    placeholderTextColor="#64748B"
                    keyboardType="numeric"
                    value={formCurrentAmount}
                    onChangeText={setFormCurrentAmount}
                  />

                  <Text style={styles.inputLabel}>Fecha Límite (AAAA-MM-DD)</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Ej. 2026-12-31"
                    placeholderTextColor="#64748B"
                    value={formDeadline}
                    onChangeText={setFormDeadline}
                  />
                </>
              )}
            </ScrollView>

            <View style={styles.modalActionRow}>
              <TouchableOpacity
                style={styles.cancelModalBtn}
                onPress={() => setIsModalVisible(false)}
                disabled={isSubmitting}
              >
                <Text style={styles.cancelModalBtnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.saveModalBtn}
                onPress={handleCreateRecord}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.saveModalBtnText}>💾 Guardar en DB</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  backBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#1E293B',
  },
  backBtnText: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
  },
  headerTitleContainer: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  headerSub: {
    color: '#64748B',
    fontSize: 11,
    marginTop: 2,
  },
  refreshBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#1E293B',
  },
  refreshBtnText: {
    fontSize: 16,
  },
  tabBarContainer: {
    backgroundColor: '#0B1120',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  tabBarContent: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: '#1E293B',
    marginRight: 6,
  },
  tabButtonActive: {
    backgroundColor: '#4F46E5',
  },
  tabIcon: {
    fontSize: 15,
    marginRight: 6,
  },
  tabTitle: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
    marginRight: 6,
  },
  tabTitleActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  tabBadge: {
    backgroundColor: '#334155',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
  },
  tabBadgeActive: {
    backgroundColor: '#6366F1',
  },
  tabBadgeText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '700',
  },
  tabBadgeTextActive: {
    color: '#FFFFFF',
  },
  errorNotice: {
    backgroundColor: '#7F1D1D',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  errorNoticeText: {
    color: '#FECACA',
    fontSize: 12,
    textAlign: 'center',
  },
  contentArea: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    color: '#94A3B8',
    fontSize: 14,
    marginTop: 12,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
  },
  emptySub: {
    color: '#64748B',
    fontSize: 13,
    textAlign: 'center',
  },
  listContent: {
    padding: 16,
    paddingBottom: 90,
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cardCompleted: {
    opacity: 0.65,
    backgroundColor: '#172554',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  cardHeaderInfo: {
    flex: 1,
    marginLeft: 10,
    marginRight: 8,
  },
  cardTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
    lineHeight: 20,
  },
  textCrossed: {
    textDecorationLine: 'line-through',
    color: '#94A3B8',
  },
  cardDesc: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 8,
    lineHeight: 18,
  },
  statusCheckbox: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: '#6366F1',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  checkboxCompleted: {
    backgroundColor: '#10B981',
    borderColor: '#10B981',
  },
  checkboxText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  badgeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 6,
  },
  pill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  priorityPill: {
    backgroundColor: '#374151',
  },
  priorityText: {
    color: '#F3F4F6',
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  categoryPill: {
    backgroundColor: '#312E81',
  },
  categoryText: {
    color: '#C7D2FE',
    fontSize: 11,
    fontWeight: '500',
  },
  duePill: {
    backgroundColor: '#064E3B',
  },
  dueText: {
    color: '#A7F3D0',
    fontSize: 11,
    fontWeight: '500',
  },
  merchantPill: {
    backgroundColor: '#701A75',
  },
  merchantText: {
    color: '#F5D0FE',
    fontSize: 11,
  },
  sourcePill: {
    backgroundColor: '#1F2937',
  },
  sourceText: {
    color: '#9CA3AF',
    fontSize: 10,
  },
  deleteBtn: {
    padding: 6,
  },
  deleteBtnText: {
    fontSize: 16,
  },
  txIconPill: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  txIncome: {
    backgroundColor: '#065F46',
  },
  txExpense: {
    backgroundColor: '#831843',
  },
  accountPillBg: {
    backgroundColor: '#1E3A8A',
  },
  emailPillBg: {
    backgroundColor: '#581C87',
  },
  goalPillBg: {
    backgroundColor: '#78350F',
  },
  txIconText: {
    fontSize: 16,
  },
  txAmount: {
    fontSize: 16,
    fontWeight: '800',
    marginTop: 2,
  },
  incomeText: {
    color: '#34D399',
  },
  expenseText: {
    color: '#F43F5E',
  },
  accountInstitution: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  accountBalanceText: {
    color: '#38BDF8',
    fontSize: 17,
    fontWeight: '800',
    marginTop: 4,
  },
  emailSender: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  unreadPill: {
    backgroundColor: '#DC2626',
  },
  readPill: {
    backgroundColor: '#475569',
  },
  statusLabel: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
  },
  goalMetaText: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '600',
    marginTop: 4,
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: '#334155',
    borderRadius: 4,
    marginTop: 8,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#F59E0B',
    borderRadius: 4,
  },
  goalDeadlineText: {
    color: '#94A3B8',
    fontSize: 11,
    marginTop: 6,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
  },
  addBtn: {
    backgroundColor: '#4F46E5',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    shadowColor: '#4F46E5',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  addBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1E293B',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    color: '#F8FAFC',
    fontSize: 17,
    fontWeight: '700',
  },
  modalCloseText: {
    color: '#94A3B8',
    fontSize: 20,
    fontWeight: '700',
    padding: 4,
  },
  modalScroll: {
    marginBottom: 16,
  },
  inputLabel: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 10,
    textTransform: 'uppercase',
  },
  textInput: {
    backgroundColor: '#0F172A',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: '#F8FAFC',
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#334155',
  },
  textArea: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  selectorRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  selectorBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#0F172A',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  selectorBtnActive: {
    backgroundColor: '#4F46E5',
    borderColor: '#6366F1',
  },
  selectorBtnText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
  },
  selectorBtnTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  modalActionRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  cancelModalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#334155',
    alignItems: 'center',
  },
  cancelModalBtnText: {
    color: '#E2E8F0',
    fontSize: 14,
    fontWeight: '600',
  },
  saveModalBtn: {
    flex: 2,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#10B981',
    alignItems: 'center',
  },
  saveModalBtnText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
  },
});
