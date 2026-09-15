import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius } from '../theme/spacing';

interface ChatBubbleProps {
  type: 'ai' | 'user';
  message: string;
  timestamp?: string;
  title?: string;
}

export function ChatBubble({ type, message, timestamp, title }: ChatBubbleProps) {
  if (type === 'ai') {
    return (
      <View style={styles.aiRow}>
        <View style={styles.aiAvatar}>
          <Text style={styles.aiAvatarIcon}>✨</Text>
        </View>
        <View style={styles.aiContent}>
          <View style={styles.aiBubble}>
            {title && (
              <View style={styles.bubbleHeader}>
                <Text style={styles.bubbleTitle}>{title}</Text>
                {timestamp && <Text style={styles.timestamp}>{timestamp}</Text>}
              </View>
            )}
            <Text style={styles.aiText}>{message}</Text>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.userRow}>
      <View style={styles.userContent}>
        <View style={styles.userBubble}>
          <Text style={styles.userText}>{message}</Text>
        </View>
        {timestamp && <Text style={styles.userTimestamp}>{timestamp}</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // AI bubble
  aiRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    maxWidth: '92%',
    alignSelf: 'flex-start',
  },
  aiAvatar: {
    width: 28,
    height: 28,
    borderRadius: BorderRadius.DEFAULT,
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.4)',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
    flexShrink: 0,
  },
  aiAvatarIcon: {
    fontSize: 13,
  },
  aiContent: {
    flex: 1,
  },
  aiBubble: {
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.lg,
    borderTopLeftRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 14,
    gap: 6,
  },
  bubbleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  bubbleTitle: {
    ...Typography.labelSm,
    color: Colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  timestamp: {
    ...Typography.labelSm,
    color: Colors.onSurfaceVariant,
    fontSize: 10,
  },
  aiText: {
    ...Typography.bodyMd,
    color: Colors.onSurface,
    lineHeight: 22,
  },

  // User bubble
  userRow: {
    alignSelf: 'flex-end',
    maxWidth: '85%',
  },
  userContent: {
    alignItems: 'flex-end',
    gap: 4,
  },
  userBubble: {
    backgroundColor: Colors.surfaceContainerHighest,
    borderRadius: BorderRadius.lg,
    borderTopRightRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.borderLight,
    padding: 14,
  },
  userText: {
    ...Typography.bodyMd,
    color: Colors.onSurface,
  },
  userTimestamp: {
    ...Typography.labelSm,
    color: Colors.onSurfaceVariant,
    fontSize: 10,
    paddingRight: 4,
  },
});
