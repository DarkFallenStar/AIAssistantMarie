import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { Colors } from '../theme/colors';

interface BudgetProgressBarProps {
  percentage: number; // 0-100
  height?: number;
}

export function BudgetProgressBar({ percentage, height = 6 }: BudgetProgressBarProps) {
  const widthAnim = useRef(new Animated.Value(0)).current;
  const isWarning = percentage >= 85;

  useEffect(() => {
    Animated.timing(widthAnim, {
      toValue: Math.min(percentage, 100),
      duration: 600,
      useNativeDriver: false,
    }).start();
  }, [percentage]);

  const fillColor = isWarning ? Colors.tertiaryContainer : Colors.primary;

  return (
    <View style={[styles.track, { height }]}>
      <Animated.View
        style={[
          styles.fill,
          {
            height,
            backgroundColor: fillColor,
            width: widthAnim.interpolate({
              inputRange: [0, 100],
              outputRange: ['0%', '100%'],
            }),
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    width: '100%',
    backgroundColor: Colors.border,
    borderRadius: 9999,
    overflow: 'hidden',
  },
  fill: {
    borderRadius: 9999,
  },
});
