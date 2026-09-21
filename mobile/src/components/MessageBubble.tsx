import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  audio_url?: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
  onSpeak?: (text: string) => void;
}

export default function MessageBubble({ message, onSpeak }: MessageBubbleProps) {
  const isUser = message.sender === 'user';

  return (
    <View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
      ]}
    >
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.assistantBubble,
        ]}
      >
        <View style={styles.senderHeader}>
          <View style={styles.senderLeft}>
            <Text
              style={[
                styles.senderText,
                isUser ? styles.userSenderText : styles.assistantSenderText,
              ]}
            >
              {isUser ? 'TÚ' : 'ASISTENTE'}
            </Text>
            {!isUser && onSpeak && (
              <TouchableOpacity
                onPress={() => onSpeak(message.text)}
                style={styles.speakerButton}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                accessibilityLabel="Escuchar respuesta"
              >
                <Text style={styles.speakerIcon}>🔊</Text>
              </TouchableOpacity>
            )}
          </View>
          <Text style={styles.timestampText}>{message.timestamp}</Text>
        </View>
        <Text style={[styles.messageText, isUser ? styles.userMessageText : styles.assistantMessageText]}>
          {message.text}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 6,
    width: '100%',
    flexDirection: 'row',
  },
  userContainer: {
    justifyContent: 'flex-end',
    paddingLeft: 40,
  },
  assistantContainer: {
    justifyContent: 'flex-start',
    paddingRight: 40,
  },
  bubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 18,
    maxWidth: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 3,
  },
  userBubble: {
    backgroundColor: '#1d4ed8',
    borderBottomRightRadius: 4,
    borderWidth: 1,
    borderColor: '#2563eb',
  },
  assistantBubble: {
    backgroundColor: '#111827',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#1f2937',
  },
  senderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
    gap: 8,
  },
  senderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  senderText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  userSenderText: {
    color: '#93c5fd',
  },
  assistantSenderText: {
    color: '#6ee7b7',
  },
  speakerButton: {
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
  speakerIcon: {
    fontSize: 12,
  },
  timestampText: {
    fontSize: 9,
    color: '#9ca3af',
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userMessageText: {
    color: '#ffffff',
  },
  assistantMessageText: {
    color: '#f3f4f6',
  },
});
