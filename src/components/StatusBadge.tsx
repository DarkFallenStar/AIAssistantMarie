import React from 'react';
import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';

export type AssistantState =
  | 'IDLE'
  | 'RECORDING'
  | 'PROCESSING'
  | 'RESPONSE'
  | 'esperando'
  | 'grabando'
  | 'procesando'
  | 'respondiendo';

interface StatusBadgeProps {
  state: AssistantState;
}

const STATE_CONFIG: Record<
  AssistantState,
  { label: string; textColor: string; bgColor: string; borderColor: string; dotColor: string }
> = {
  IDLE: {
    label: 'IDLE • En espera',
    textColor: '#82aaff',
    bgColor: '#0f172a',
    borderColor: '#1e3a8a',
    dotColor: '#3b82f6',
  },
  RECORDING: {
    label: 'RECORDING • Grabando...',
    textColor: '#ff5370',
    bgColor: '#2a0e14',
    borderColor: '#881337',
    dotColor: '#ef4444',
  },
  PROCESSING: {
    label: 'PROCESSING • Procesando...',
    textColor: '#ffcb6b',
    bgColor: '#2a220e',
    borderColor: '#78350f',
    dotColor: '#f59e0b',
  },
  RESPONSE: {
    label: 'RESPONSE • Respondiendo...',
    textColor: '#4ade80',
    bgColor: '#0c2419',
    borderColor: '#065f46',
    dotColor: '#10b981',
  },
  esperando: {
    label: 'IDLE • En espera',
    textColor: '#82aaff',
    bgColor: '#0f172a',
    borderColor: '#1e3a8a',
    dotColor: '#3b82f6',
  },
  grabando: {
    label: 'RECORDING • Grabando...',
    textColor: '#ff5370',
    bgColor: '#2a0e14',
    borderColor: '#881337',
    dotColor: '#ef4444',
  },
  procesando: {
    label: 'PROCESSING • Procesando...',
    textColor: '#ffcb6b',
    bgColor: '#2a220e',
    borderColor: '#78350f',
    dotColor: '#f59e0b',
  },
  respondiendo: {
    label: 'RESPONSE • Respondiendo...',
    textColor: '#4ade80',
    bgColor: '#0c2419',
    borderColor: '#065f46',
    dotColor: '#10b981',
  },
};

export default function StatusBadge({ state }: StatusBadgeProps) {
  const config = STATE_CONFIG[state];

  return (
    <View
      style={[
        styles.badgeContainer,
        {
          backgroundColor: config.bgColor,
          borderColor: config.borderColor,
        },
      ]}
    >
      {state === 'procesando' ? (
        <ActivityIndicator size="small" color={config.dotColor} style={styles.indicator} />
      ) : (
        <View style={[styles.dot, { backgroundColor: config.dotColor }]} />
      )}
      <Text style={[styles.label, { color: config.textColor }]}>{config.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    alignSelf: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  indicator: {
    transform: [{ scale: 0.7 }],
    marginRight: 4,
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
});
