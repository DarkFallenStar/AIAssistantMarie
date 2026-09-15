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
import { CategoryCard } from '../components/CategoryCard';
import { GoalCard } from '../components/GoalCard';
import { TransactionItem } from '../components/TransactionItem';

const CATEGORIES = [
  { icon: 'restaurant', name: 'Alimentación Campus', spent: 142, total: 220 },
  { icon: 'directions_bus', name: 'Transporte Universitario', spent: 38.5, total: 60 },
  { icon: 'auto_stories', name: 'Materiales & Libros', spent: 45, total: 80 },
  { icon: 'celebration', name: 'Ocio & Vida Social', spent: 64, total: 100 },
];

const GOALS = [
  { icon: 'laptop_mac', name: 'Laptop Semestre', saved: 620, total: 900, subtitle: 'Meta en 42 días 🎯' },
  { icon: 'shield', name: 'Fondo Emergencia', saved: 150, total: 300, subtitle: 'Ahorro protegido' },
];

const TRANSACTIONS = [
  { icon: 'lunch_dining', name: 'Almuerzo Facultad', subtitle: 'Hace 2h · Voz clasificada', amount: 6.5, isExpense: true },
  { icon: 'print', name: 'Fotocopias Cálculo', subtitle: 'Ayer · Clasificado por texto', amount: 3.2, isExpense: true },
];

export function DashboardScreen() {
  const insets = useSafeAreaInsets();
  const [inputText, setInputText] = useState('');
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
              <Text style={styles.statusText}>SISTEMA OPERATIVO</Text>
            </View>
          </View>
        </View>

        <View style={styles.headerRight}>
          <View style={styles.modeContainer}>
            <Text style={styles.modeLabel}>MODO</Text>
            <Text style={styles.modeValue}>Analítico</Text>
          </View>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>S</Text>
          </View>
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + 100 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Title & Cycle Status */}
        <View style={styles.greetingRow}>
          <View>
            <Text style={styles.pageTitle}>Resumen Mensual</Text>
            <Text style={styles.pageSubtitle}>Usuario: Sofía · Periodo actual de facturación</Text>
          </View>
          <View style={styles.dayPill}>
            <View style={styles.dayDot} />
            <Text style={styles.dayText}>Día 14 / 30</Text>
          </View>
        </View>

        {/* Hero Balance Card */}
        <View style={styles.heroCard}>
          <View style={styles.heroGlow} />
          <View style={styles.heroInner}>
            {/* Top Row */}
            <View style={styles.heroTopRow}>
              <Text style={styles.heroTopLabel}>SALDO DISPONIBLE DEL CICLO</Text>
              <View style={styles.optimoBadge}>
                <Text style={styles.optimoIcon}>✓</Text>
                <Text style={styles.optimoText}>Desviación 0.0%</Text>
              </View>
            </View>

            {/* Main Balance Display */}
            <View style={styles.heroBalanceRow}>
              <Text style={styles.heroAmount}>$480.00</Text>
              <Text style={styles.heroCurrency}>USD</Text>
            </View>

            {/* Inset Daily Recommendation */}
            <View style={styles.dailyBox}>
              <View style={styles.dailyLeft}>
                <View style={styles.dailyIconBox}>
                  <Text style={styles.dailyIcon}>📊</Text>
                </View>
                <View>
                  <Text style={styles.dailyBoxLabel}>Límite diario sugerido</Text>
                  <Text style={styles.dailyBoxAmount}>$16.50 USD / día</Text>
                </View>
              </View>
              <View style={styles.trendBadge}>
                <Text style={styles.trendText}>📈 +2.4%</Text>
              </View>
            </View>

            {/* Budget Progress Bar */}
            <View style={styles.budgetProgressSection}>
              <View style={styles.budgetLabelsRow}>
                <Text style={styles.budgetExecText}>Ejecutado: 38% · Restante: 62%</Text>
                <Text style={styles.budgetBaseText}>$775.00 Base</Text>
              </View>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: '62%' }]} />
              </View>
            </View>
          </View>
        </View>

        {/* Quick Expense Input */}
        <View style={styles.quickInputCard}>
          <Text style={styles.inputLeadingIcon}>⌨️</Text>
          <TextInput
            style={styles.quickTextInput}
            placeholder="Registrar monto y concepto (ej. $8.00 transporte)..."
            placeholderTextColor={Colors.onSurfaceVariant + '99'}
            value={inputText}
            onChangeText={setInputText}
          />
          <TouchableOpacity style={styles.micInputBtn} activeOpacity={0.8}>
            <Text style={styles.micInputIcon}>🎙️</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.sendInputBtn} activeOpacity={0.8}>
            <Text style={styles.sendInputIcon}>↵</Text>
          </TouchableOpacity>
        </View>

        {/* Categories Section */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Distribución de Gastos</Text>
            <Text style={styles.sectionSubtitle}>Control presupuestario por categoría académica</Text>
          </View>
          <TouchableOpacity style={styles.seeAllBtn} activeOpacity={0.7}>
            <Text style={styles.seeAllText}>Ver desglose</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.listContainer}>
          {CATEGORIES.map((cat) => (
            <CategoryCard key={cat.name} {...cat} />
          ))}
        </View>

        {/* Goals Section */}
        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionTitle}>Metas Activas</Text>
            <Text style={styles.sectionSubtitle}>2 en progreso constante</Text>
          </View>
        </View>
        <View style={styles.goalsRow}>
          {GOALS.map((goal) => (
            <GoalCard key={goal.name} {...goal} />
          ))}
        </View>

        {/* Recent Activity Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.activityTitleRow}>
            <Text style={styles.sectionTitle}>Actividad Reciente</Text>
            <View style={styles.aiTag}>
              <Text style={styles.aiTagText}>IA</Text>
            </View>
          </View>
          <TouchableOpacity activeOpacity={0.7}>
            <Text style={styles.seeAllText}>Historial</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.listContainer}>
          {TRANSACTIONS.map((tx) => (
            <TransactionItem key={tx.name} {...tx} />
          ))}
        </View>
      </ScrollView>
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
    ...Typography.headlineSm,
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

  // Scroll
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    gap: Spacing.md,
    paddingTop: Spacing.sm,
  },

  // Greeting
  greetingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 4,
  },
  pageTitle: {
    ...Typography.headlineMd,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  pageSubtitle: {
    ...Typography.bodySm,
    color: Colors.onSurfaceVariant,
    marginTop: 2,
  },
  dayPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.DEFAULT,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  dayDot: {
    width: 6,
    height: 6,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primary,
  },
  dayText: {
    fontSize: 11,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },

  // Hero Card
  heroCard: {
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
    position: 'relative',
  },
  heroGlow: {
    position: 'absolute',
    right: -40,
    top: -40,
    width: 140,
    height: 140,
    borderRadius: BorderRadius.full,
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
  },
  heroInner: {
    padding: 18,
    gap: 14,
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  heroTopLabel: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
    fontFamily: 'PlusJakartaSans_600SemiBold',
    letterSpacing: 0.8,
  },
  optimoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  optimoIcon: {
    fontSize: 10,
    color: Colors.primary,
  },
  optimoText: {
    fontSize: 11,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  heroBalanceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  heroAmount: {
    fontSize: 34,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_800ExtraBold',
    letterSpacing: -0.5,
  },
  heroCurrency: {
    fontSize: 13,
    color: Colors.onSurfaceVariant,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },

  // Daily Box Inset
  dailyBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.surfaceContainerHigh,
    borderRadius: BorderRadius.DEFAULT,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 10,
  },
  dailyLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dailyIconBox: {
    width: 32,
    height: 32,
    borderRadius: BorderRadius.sm,
    backgroundColor: Colors.surfaceContainer,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dailyIcon: {
    fontSize: 14,
  },
  dailyBoxLabel: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
  },
  dailyBoxAmount: {
    fontSize: 13,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  trendText: {
    fontSize: 12,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },

  // Progress Section
  budgetProgressSection: {
    gap: 6,
    paddingTop: 2,
  },
  budgetLabelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  budgetExecText: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
  },
  budgetBaseText: {
    fontSize: 11,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  progressTrack: {
    width: '100%',
    height: 6,
    backgroundColor: Colors.border,
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.full,
  },

  // Quick Input Card
  quickInputCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: 12,
    paddingVertical: 6,
    gap: 8,
  },
  inputLeadingIcon: {
    fontSize: 16,
  },
  quickTextInput: {
    flex: 1,
    ...Typography.bodyMd,
    color: Colors.onSurface,
    paddingVertical: 6,
    fontSize: 13,
  },
  micInputBtn: {
    width: 34,
    height: 34,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micInputIcon: {
    fontSize: 15,
  },
  sendInputBtn: {
    width: 34,
    height: 34,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendInputIcon: {
    fontSize: 16,
    color: Colors.onPrimary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },

  // Sections
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  sectionTitle: {
    ...Typography.headlineSm,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
    fontSize: 17,
  },
  sectionSubtitle: {
    ...Typography.bodySm,
    color: Colors.onSurfaceVariant,
    marginTop: 1,
    fontSize: 12,
  },
  seeAllBtn: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  seeAllText: {
    fontSize: 11,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  listContainer: {
    gap: Spacing.xs,
  },
  goalsRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  activityTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  aiTag: {
    paddingHorizontal: 6,
    paddingVertical: 1,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: BorderRadius.sm,
  },
  aiTagText: {
    fontSize: 10,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
});
