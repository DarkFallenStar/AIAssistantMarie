import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Animated,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius, Spacing } from '../theme/spacing';
import { ChatBubble } from '../components/ChatBubble';

const QUICK_CHIPS = [
  { icon: '🎯', label: '¿Cómo voy con mi meta?' },
  { icon: '📊', label: 'Resumen semanal' },
  { icon: '➕', label: 'Registrar ingreso' },
  { icon: '💡', label: 'Consejo de ahorro' },
];

const INITIAL_MESSAGES = [
  {
    id: '1',
    type: 'ai' as const,
    title: 'MiMentor IA · Balance del día',
    message:
      '¡Hola Sofía! Vas excelente hoy: has registrado solo $4.50 de tu margen previsto de $16.50. ¿Deseas proyectar gastos del fin de semana o registrar alguna compra?',
    timestamp: '09:14 AM',
  },
  {
    id: '2',
    type: 'user' as const,
    message: '¿Cuánto puedo gastar el fin de semana si voy al cine el sábado? 🎬',
    timestamp: '09:18 AM',
  },
  {
    id: '3',
    type: 'ai' as const,
    title: 'MiMentor IA · Proyección Inteligente',
    message:
      'Si mantienes tu consumo universitario de jueves y viernes por debajo de $14/día, tendrás $35.00 libres para el cine sin alterar tu meta de ahorro de la laptop 🍿.',
    timestamp: '09:18 AM',
  },
];

interface Message {
  id: string;
  type: 'ai' | 'user';
  message: string;
  timestamp?: string;
  title?: string;
}

export function ChatScreen() {
  const insets = useSafeAreaInsets();
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const scrollRef = useRef<ScrollView>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.35, duration: 800, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, []);

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    const now = new Date();
    const timeStr = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });

    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      message: text,
      timestamp: timeStr,
    };
    const aiReply: Message = {
      id: (Date.now() + 1).toString(),
      type: 'ai',
      title: 'MiMentor IA · Análisis Activo',
      message: `He registrado tu solicitud: "${text}". Analizando impacto en tu presupuesto universitario... Todo en orden.`,
      timestamp: timeStr,
    };

    setMessages((prev) => [...prev, userMsg, aiReply]);
    setInputText('');
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
  };

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.background} />

      {/* Header Fijo */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoIcon}>⚡</Text>
          </View>
          <View>
            <Text style={styles.logoText}>MiMentor</Text>
            <View style={styles.statusRow}>
              <Animated.View style={[styles.statusDot, { transform: [{ scale: pulseAnim }] }]} />
              <Text style={styles.statusText}>SISTEMA ACTIVO</Text>
            </View>
          </View>
        </View>

        <View style={styles.headerRight}>
          <View style={styles.modeContainer}>
            <Text style={styles.modeLabel}>MÓDULO</Text>
            <Text style={styles.modeValue}>Terminal IA</Text>
          </View>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>S</Text>
          </View>
        </View>
      </View>

      {/* Tarjeta Contextual Superior (Motor de Cálculo IA) */}
      <View style={styles.contextCard}>
        <View style={styles.contextTopRow}>
          <View style={styles.contextStatusLeft}>
            <Animated.View style={[styles.pulseCircle, { transform: [{ scale: pulseAnim }] }]} />
            <Text style={styles.contextTitle}>MOTOR DE CÁLCULO IA</Text>
          </View>
          <View style={styles.contextSecurity}>
            <Text style={styles.lockIcon}>🔒</Text>
            <Text style={styles.securityText}>TLS 1.3 / Cifrado</Text>
          </View>
        </View>

        {/* Píldora de Presupuesto Activo */}
        <View style={styles.budgetMarginBox}>
          <View style={styles.budgetLeft}>
            <View style={styles.walletBadge}>
              <Text style={styles.walletIcon}>👛</Text>
            </View>
            <View>
              <Text style={styles.budgetBoxLabel}>MARGEN SEMANAL</Text>
              <Text style={styles.budgetBoxAmount}>
                $115.50 <Text style={styles.budgetBoxSub}>disponible</Text>
              </Text>
            </View>
          </View>
          <View style={styles.favorBadge}>
            <Text style={styles.favorText}>82% margen</Text>
          </View>
        </View>
      </View>

      {/* Chat Feed */}
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 170 }]}
        showsVerticalScrollIndicator={false}
      >
        {messages.map((msg) => (
          <ChatBubble
            key={msg.id}
            type={msg.type}
            message={msg.message}
            timestamp={msg.timestamp}
            title={msg.title}
          />
        ))}
      </ScrollView>

      {/* Barra Inferior Fija de Entrada */}
      <View style={[styles.bottomArea, { paddingBottom: insets.bottom + 85 }]}>
        {/* Chips de Preguntas Rápidas */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipsContent}
          style={styles.chips}
        >
          {QUICK_CHIPS.map((chip) => (
            <TouchableOpacity
              key={chip.label}
              style={styles.chip}
              activeOpacity={0.7}
              onPress={() => sendMessage(chip.label)}
            >
              <Text style={styles.chipIcon}>{chip.icon}</Text>
              <Text style={styles.chipLabel}>{chip.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Input Bar */}
        <View style={styles.inputBar}>
          <TouchableOpacity style={styles.micButton} activeOpacity={0.8}>
            <Animated.View style={[styles.micPulse, { transform: [{ scale: pulseAnim }] }]} />
            <Text style={styles.micIcon}>🎙️</Text>
          </TouchableOpacity>
          <TextInput
            style={styles.textInput}
            placeholder="Habla o escribe a tu copiloto..."
            placeholderTextColor={Colors.onSurfaceVariant + '99'}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => sendMessage(inputText)}
            returnKeyType="send"
          />
          <TouchableOpacity
            style={styles.sendButton}
            activeOpacity={0.8}
            onPress={() => sendMessage(inputText)}
          >
            <Text style={styles.sendIcon}>➤</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  // Header
  header: {
    height: 60,
    paddingHorizontal: Spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.background,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  logoBadge: {
    width: 36,
    height: 36,
    borderRadius: BorderRadius.sm,
    backgroundColor: Colors.surfaceContainer,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoIcon: {
    fontSize: 16,
  },
  logoText: {
    color: Colors.onSurface,
    fontSize: 17,
    fontFamily: 'PlusJakartaSans_700Bold',
    lineHeight: 20,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 2,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primary,
  },
  statusText: {
    fontSize: 10,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
    letterSpacing: 0.8,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  modeContainer: {
    alignItems: 'flex-end',
  },
  modeLabel: {
    fontSize: 9,
    color: Colors.onSurfaceVariant,
    letterSpacing: 0.8,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  modeValue: {
    fontSize: 12,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  avatarCircle: {
    width: 34,
    height: 34,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: Colors.primary,
    fontSize: 14,
    fontFamily: 'PlusJakartaSans_700Bold',
  },

  // Context Card
  contextCard: {
    marginHorizontal: Spacing.md,
    marginTop: Spacing.sm,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 12,
    gap: 10,
  },
  contextTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  contextStatusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pulseCircle: {
    width: 7,
    height: 7,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primary,
  },
  contextTitle: {
    fontSize: 11,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
    letterSpacing: 0.6,
  },
  contextSecurity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  lockIcon: {
    fontSize: 11,
  },
  securityText: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
    fontFamily: 'PlusJakartaSans_500Medium',
  },
  budgetMarginBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.surfaceContainerHigh,
    borderRadius: BorderRadius.DEFAULT,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 10,
  },
  budgetLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  walletBadge: {
    width: 32,
    height: 32,
    borderRadius: BorderRadius.sm,
    backgroundColor: Colors.surfaceContainer,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  walletIcon: {
    fontSize: 14,
  },
  budgetBoxLabel: {
    fontSize: 10,
    color: Colors.onSurfaceVariant,
    letterSpacing: 0.6,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  budgetBoxAmount: {
    fontSize: 15,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  budgetBoxSub: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
    fontFamily: 'PlusJakartaSans_400Regular',
  },
  favorBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  favorText: {
    fontSize: 11,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },

  // Chat Feed
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.sm,
    gap: Spacing.md,
  },

  // Bottom Area
  bottomArea: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: Spacing.md,
    gap: 8,
    backgroundColor: Colors.background,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    paddingTop: 8,
  },
  chips: {
    flexGrow: 0,
  },
  chipsContent: {
    gap: 8,
    paddingBottom: 2,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipIcon: {
    fontSize: 13,
  },
  chipLabel: {
    fontSize: 12,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_500Medium',
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 6,
    gap: 8,
  },
  micButton: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  micPulse: {
    position: 'absolute',
    width: 38,
    height: 38,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
  },
  micIcon: {
    fontSize: 16,
  },
  textInput: {
    flex: 1,
    color: Colors.onSurface,
    paddingVertical: 4,
    fontSize: 13,
    fontFamily: 'PlusJakartaSans_400Regular',
  },
  sendButton: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendIcon: {
    fontSize: 14,
    color: Colors.onPrimary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
});
