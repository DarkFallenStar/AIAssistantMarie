import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius, Spacing } from '../theme/spacing';

interface TransactionItemProps {
  icon: string;
  name: string;
  subtitle: string;
  amount: number;
  isExpense?: boolean;
}

const ICON_MAP: Record<string, string> = {
  lunch_dining: '🥗',
  print: '🖨️',
  restaurant: '🍽️',
  directions_bus: '🚌',
  coffee: '☕',
  default: '💸',
};

export function TransactionItem({
  icon,
  name,
  subtitle,
  amount,
  isExpense = true,
}: TransactionItemProps) {
  return (
    <View style={styles.container}>
      <View style={styles.left}>
        <View style={styles.iconCircle}>
          <Text style={styles.iconEmoji}>{ICON_MAP[icon] ?? ICON_MAP.default}</Text>
        </View>
        <View style={styles.details}>
          <Text style={styles.name}>{name}</Text>
          <View style={styles.subtitleRow}>
            <View style={styles.tag}>
              <Text style={styles.tagText}>IA</Text>
            </View>
            <Text style={styles.subtitle}>{subtitle}</Text>
          </View>
        </View>
      </View>
      <Text style={[styles.amount, isExpense ? styles.expense : styles.income]}>
        {isExpense ? '-' : '+'}${Math.abs(amount).toFixed(2)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.sm,
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    flex: 1,
  },
  iconCircle: {
    width: 38,
    height: 38,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 18,
  },
  details: {
    flex: 1,
  },
  name: {
    ...Typography.labelLg,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  subtitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 2,
  },
  tag: {
    paddingHorizontal: 5,
    paddingVertical: 1,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: BorderRadius.sm,
  },
  tagText: {
    fontSize: 9,
    fontFamily: 'PlusJakartaSans_700Bold',
    color: Colors.primary,
  },
  subtitle: {
    ...Typography.bodySm,
    fontSize: 11,
    color: Colors.onSurfaceVariant,
  },
  amount: {
    ...Typography.labelLg,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  expense: {
    color: Colors.error,
  },
  income: {
    color: Colors.primary,
  },
});
