import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius, Spacing } from '../theme/spacing';
import { BudgetProgressBar } from './BudgetProgressBar';

interface GoalCardProps {
  icon: string;
  name: string;
  saved: number;
  total: number;
  subtitle: string;
}

const ICON_MAP: Record<string, string> = {
  laptop_mac: '💻',
  shield: '🛡️',
  flag: '🎯',
  default: '⭐',
};

export function GoalCard({ icon, name, saved, total, subtitle }: GoalCardProps) {
  const percentage = Math.round((saved / total) * 100);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.iconBox}>
          <Text style={styles.iconEmoji}>{ICON_MAP[icon] ?? ICON_MAP.default}</Text>
        </View>
        <View style={styles.badge}>
          <Text style={styles.percentage}>{percentage}%</Text>
        </View>
      </View>
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={1}>
          {name}
        </Text>
        <Text style={styles.amounts}>
          ${saved} <Text style={styles.amountsTotal}>/ ${total} USD</Text>
        </Text>
      </View>
      <View style={styles.progressSection}>
        <BudgetProgressBar percentage={percentage} height={5} />
        <Text style={styles.subtitle}>{subtitle}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.sm + 2,
    gap: Spacing.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: Colors.surfaceContainerHigh,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 16,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  percentage: {
    ...Typography.labelSm,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  info: {
    gap: 2,
  },
  name: {
    ...Typography.labelLg,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  amounts: {
    ...Typography.labelLg,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  amountsTotal: {
    ...Typography.labelSm,
    color: Colors.onSurfaceVariant,
    fontFamily: 'PlusJakartaSans_400Regular',
  },
  progressSection: {
    gap: 6,
  },
  subtitle: {
    ...Typography.bodySm,
    fontSize: 11,
    color: Colors.onSurfaceVariant,
  },
});
