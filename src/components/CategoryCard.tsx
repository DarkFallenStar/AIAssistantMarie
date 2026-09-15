import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius, Spacing } from '../theme/spacing';
import { BudgetProgressBar } from './BudgetProgressBar';

interface CategoryCardProps {
  icon: string;
  name: string;
  spent: number;
  total: number;
}

const ICON_MAP: Record<string, string> = {
  restaurant: '🍽️',
  directions_bus: '🚌',
  auto_stories: '📚',
  celebration: '🎉',
  laptop_mac: '💻',
  shield: '🛡️',
  mic: '🎤',
  default: '💰',
};

export function CategoryCard({ icon, name, spent, total }: CategoryCardProps) {
  const percentage = Math.round((spent / total) * 100);
  const remaining = total - spent;

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <View style={styles.left}>
          <View style={styles.iconContainer}>
            <Text style={styles.iconEmoji}>{ICON_MAP[icon] ?? ICON_MAP.default}</Text>
          </View>
          <View style={styles.infoCol}>
            <Text style={styles.name}>{name}</Text>
            <Text style={styles.amounts}>
              ${spent.toFixed(2)} / ${total.toFixed(2)} USD
            </Text>
          </View>
        </View>
        <View style={styles.right}>
          <Text style={styles.percentage}>{percentage}%</Text>
          <Text style={styles.remaining}>Resta ${remaining.toFixed(0)}</Text>
        </View>
      </View>
      <BudgetProgressBar percentage={percentage} height={5} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.sm + 2,
    gap: Spacing.xs + 2,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    flex: 1,
  },
  iconContainer: {
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
  infoCol: {
    flex: 1,
  },
  name: {
    ...Typography.labelLg,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_600SemiBold',
  },
  amounts: {
    ...Typography.bodySm,
    color: Colors.onSurfaceVariant,
    marginTop: 2,
    fontSize: 12,
  },
  right: {
    alignItems: 'flex-end',
  },
  percentage: {
    ...Typography.labelLg,
    color: Colors.onSurface,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  remaining: {
    ...Typography.labelSm,
    color: Colors.onSurfaceVariant,
    fontSize: 11,
    marginTop: 2,
  },
});
