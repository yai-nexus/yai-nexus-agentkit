import { openDB, DBSchema, IDBPDatabase } from 'idb';

/**
 * Database schema for storing chat conversations
 */
interface ChatDB extends DBSchema {
  conversations: {
    key: string; // conversationId
    value: {
      id: string;
      userId: string;
      title?: string;
      messages: ChatMessage[];
      createdAt: number;
      updatedAt: number;
    };
    indexes: {
      'by-user': string; // userId
      'by-updated': number; // updatedAt
    };
  };
  messages: {
    key: string; // messageId
    value: ChatMessage;
    indexes: {
      'by-conversation': string; // conversationId
      'by-timestamp': number; // timestamp
    };
  };
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface ConversationData {
  id: string;
  userId: string;
  title?: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

/**
 * Storage manager for persisting chat conversations in IndexedDB
 */
export class ChatStorage {
  private db: IDBPDatabase<ChatDB> | null = null;
  private dbName: string;
  private dbVersion: number;

  constructor(dbName = 'yai-nexus-chat', dbVersion = 1) {
    this.dbName = dbName;
    this.dbVersion = dbVersion;
  }

  /**
   * Initialize the database connection
   */
  async init(): Promise<void> {
    if (this.db) return;

    try {
      this.db = await openDB<ChatDB>(this.dbName, this.dbVersion, {
        upgrade(db) {
          // Create conversations store
          if (!db.objectStoreNames.contains('conversations')) {
            const conversationStore = db.createObjectStore('conversations', {
              keyPath: 'id',
            });
            conversationStore.createIndex('by-user', 'userId');
            conversationStore.createIndex('by-updated', 'updatedAt');
          }

          // Create messages store
          if (!db.objectStoreNames.contains('messages')) {
            const messageStore = db.createObjectStore('messages', {
              keyPath: 'id',
            });
            messageStore.createIndex('by-conversation', 'conversationId');
            messageStore.createIndex('by-timestamp', 'timestamp');
          }
        },
      });
    } catch (error) {
      console.error('Failed to initialize ChatStorage:', error);
      throw error;
    }
  }

  /**
   * Save a conversation to storage
   */
  async saveConversation(conversation: ConversationData): Promise<void> {
    await this.ensureInitialized();
    
    const tx = this.db!.transaction(['conversations', 'messages'], 'readwrite');
    
    try {
      // Save conversation metadata
      await tx.objectStore('conversations').put(conversation);
      
      // Save all messages
      const messageStore = tx.objectStore('messages');
      for (const message of conversation.messages) {
        await messageStore.put(message);
      }
      
      await tx.done;
    } catch (error) {
      console.error('Failed to save conversation:', error);
      throw error;
    }
  }

  /**
   * Load a conversation from storage
   */
  async loadConversation(conversationId: string): Promise<ConversationData | null> {
    await this.ensureInitialized();
    
    try {
      const conversation = await this.db!.get('conversations', conversationId);
      if (!conversation) return null;

      // Load messages for this conversation
      const messages = await this.db!.getAllFromIndex(
        'messages',
        'by-conversation',
        conversationId
      );

      // Sort messages by timestamp
      messages.sort((a, b) => a.timestamp - b.timestamp);

      return {
        ...conversation,
        messages,
      };
    } catch (error) {
      console.error('Failed to load conversation:', error);
      return null;
    }
  }

  /**
   * Add a message to a conversation
   */
  async addMessage(message: ChatMessage): Promise<void> {
    await this.ensureInitialized();
    
    const tx = this.db!.transaction(['conversations', 'messages'], 'readwrite');
    
    try {
      // Save the message
      await tx.objectStore('messages').put(message);
      
      // Update conversation's updatedAt timestamp
      const conversation = await tx.objectStore('conversations').get(message.conversationId);
      if (conversation) {
        conversation.updatedAt = message.timestamp;
        await tx.objectStore('conversations').put(conversation);
      }
      
      await tx.done;
    } catch (error) {
      console.error('Failed to add message:', error);
      throw error;
    }
  }

  /**
   * Get all conversations for a user
   */
  async getUserConversations(userId: string): Promise<ConversationData[]> {
    await this.ensureInitialized();
    
    try {
      const conversations = await this.db!.getAllFromIndex(
        'conversations',
        'by-user',
        userId
      );

      // Sort by most recently updated
      conversations.sort((a, b) => b.updatedAt - a.updatedAt);

      // Load messages for each conversation
      const conversationsWithMessages = await Promise.all(
        conversations.map(async (conv) => {
          const messages = await this.db!.getAllFromIndex(
            'messages',
            'by-conversation',
            conv.id
          );
          messages.sort((a, b) => a.timestamp - b.timestamp);
          
          return {
            ...conv,
            messages,
          };
        })
      );

      return conversationsWithMessages;
    } catch (error) {
      console.error('Failed to get user conversations:', error);
      return [];
    }
  }

  /**
   * Delete a conversation and all its messages
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await this.ensureInitialized();
    
    const tx = this.db!.transaction(['conversations', 'messages'], 'readwrite');
    
    try {
      // Delete conversation
      await tx.objectStore('conversations').delete(conversationId);
      
      // Delete all messages in the conversation
      const messageStore = tx.objectStore('messages');
      const messages = await messageStore.index('by-conversation').getAll(conversationId);
      
      for (const message of messages) {
        await tx.objectStore('messages').delete(message.id);
      }
      
      await tx.done;
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  }

  /**
   * Clear all data for a user
   */
  async clearUserData(userId: string): Promise<void> {
    await this.ensureInitialized();
    
    try {
      const conversations = await this.getUserConversations(userId);
      
      for (const conversation of conversations) {
        await this.deleteConversation(conversation.id);
      }
    } catch (error) {
      console.error('Failed to clear user data:', error);
      throw error;
    }
  }

  /**
   * Close the database connection
   */
  async close(): Promise<void> {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }

  /**
   * Ensure the database is initialized
   */
  private async ensureInitialized(): Promise<void> {
    if (!this.db) {
      await this.init();
    }
  }

  /**
   * Generate a unique message ID
   */
  static generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate a unique conversation ID
   */
  static generateConversationId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}