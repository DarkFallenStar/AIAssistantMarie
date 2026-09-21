import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, TouchableOpacity, Text, Animated, Easing } from 'react-native';
import { AssistantState } from './StatusBadge';

interface MicButtonProps {
  state: AssistantState;
  onPress: () => void;
  disabled?: boolean;
}

export default function MicButton({ state, onPress, disabled }: MicButtonProps) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(0.6)).current;

  const isRecording = state === 'RECORDING' || state === 'grabando';
  const isProcessing = state === 'PROCESSING' || state === 'procesando';
  const isResponding = state === 'RESPONSE' || state === 'respondiendo';

  useEffect(() => {
    let animation: Animated.CompositeAnimation | null = null;

    if (isRecording) {
      // Rapid intense pulse for recording
      animation = Animated.loop(
        Animated.parallel([
          Animated.sequence([
            Animated.timing(pulseAnim, {
              toValue: 1.4,
              duration: 700,
              easing: Easing.out(Easing.ease),
              useNativeDriver: true,
            }),
            Animated.timing(pulseAnim, {
              toValue: 1.0,
              duration: 700,
              easing: Easing.in(Easing.ease),
              useNativeDriver: true,
            }),
          ]),
          Animated.sequence([
            Animated.timing(opacityAnim, {
              toValue: 0.2,
              duration: 700,
              useNativeDriver: true,
            }),
            Animated.timing(opacityAnim, {
              toValue: 0.8,
              duration: 700,
              useNativeDriver: true,
            }),
          ]),
        ])
      );
      animation.start();
    } else if (isProcessing || isResponding) {
      // Gentle breathing pulse
      animation = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 900,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1.0,
            duration: 900,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      );
      animation.start();
    } else {
      // Idle state
      pulseAnim.setValue(1);
      opacityAnim.setValue(0.3);
    }

    return () => {
      animation?.stop();
    };
  }, [state]);

  const getThemeColors = () => {
    if (isRecording) {
      return {
        buttonBg: '#dc2626',
        ringBg: '#ef4444',
        borderColor: '#f87171',
        shadowColor: '#ef4444',
      };
    }
    if (isProcessing) {
      return {
        buttonBg: '#d97706',
        ringBg: '#f59e0b',
        borderColor: '#fbbf24',
        shadowColor: '#f59e0b',
      };
    }
    if (isResponding) {
      return {
        buttonBg: '#059669',
        ringBg: '#10b981',
        borderColor: '#34d399',
        shadowColor: '#10b981',
      };
    }
    return {
      buttonBg: '#2563eb',
      ringBg: '#3b82f6',
      borderColor: '#60a5fa',
      shadowColor: '#3b82f6',
    };
  };

  const theme = getThemeColors();

  return (
    <View style={styles.outerContainer}>
      {/* Halo animado */}
      <Animated.View
        style={[
          styles.haloRing,
          {
            backgroundColor: theme.ringBg,
            opacity: opacityAnim,
            transform: [{ scale: pulseAnim }],
          },
        ]}
      />

      {/* Botón Principal */}
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={onPress}
        disabled={disabled || isProcessing}
        style={[
          styles.button,
          {
            backgroundColor: theme.buttonBg,
            borderColor: theme.borderColor,
            shadowColor: theme.shadowColor,
          },
          (disabled || isProcessing) && styles.disabledButton,
        ]}
      >
        <Text style={styles.micIcon}>
          {isRecording ? '⏹️' : isProcessing ? '⏳' : isResponding ? '🔊' : '🎙️'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  outerContainer: {
    width: 96,
    height: 96,
    justifyContent: 'center',
    alignItems: 'center',
  },
  haloRing: {
    position: 'absolute',
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  button: {
    width: 68,
    height: 68,
    borderRadius: 34,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 8,
  },
  disabledButton: {
    opacity: 0.7,
  },
  micIcon: {
    fontSize: 28,
  },
});
