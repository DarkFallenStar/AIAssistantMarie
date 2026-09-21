import { File, Paths } from 'expo-file-system';
import { ChatMessage } from '../components/MessageBubble';

const CHAT_STORAGE_FILENAME = 'assistant_chat_history.json';

/**
 * Service for persisting chat history locally using Expo File System modern File API.
 * Ensures conversation messages survive mobile app closures and reloads in Expo Go.
 */
export async function loadChatHistory(): Promise<ChatMessage[]> {
  try {
    const file = new File(Paths.document, CHAT_STORAGE_FILENAME);
    if (!file.exists) {
      return [];
    }
    const rawContent = await file.text();
    if (!rawContent || !rawContent.trim()) {
      return [];
    }
    const parsed = JSON.parse(rawContent);
    if (Array.isArray(parsed)) {
      return parsed;
    }
    return [];
  } catch (err) {
    console.warn('[ChatStorage] Error loading chat history:', err);
    return [];
  }
}

export async function saveChatHistory(messages: ChatMessage[]): Promise<boolean> {
  try {
    const file = new File(Paths.document, CHAT_STORAGE_FILENAME);
    const jsonStr = JSON.stringify(messages || []);
    if (!file.exists) {
      file.create();
    }
    await file.write(jsonStr);
    return true;
  } catch (err) {
    console.warn('[ChatStorage] Error saving chat history:', err);
    return false;
  }
}

export async function clearChatHistory(): Promise<boolean> {
  try {
    const file = new File(Paths.document, CHAT_STORAGE_FILENAME);
    if (file.exists) {
      await file.delete();
    }
    return true;
  } catch (err) {
    console.warn('[ChatStorage] Error clearing chat history:', err);
    return false;
  }
}
