"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { ChatStorage, ChatMessage, ConversationData } from './storage';

export interface YaiNexusPersistenceProviderProps {
  userId: string;
  conversationId: string;
  children: React.ReactNode;
  autoSave?: boolean;
  dbName?: string;
}

export interface PersistenceContextValue {
  storage: ChatStorage | null;
  conversation: ConversationData | null;
  isLoading: boolean;
  saveMessage: (message: Omit<ChatMessage, 'id' | 'conversationId' | 'timestamp'>) => Promise<void>;
  loadConversation: () => Promise<void>;
  clearConversation: () => Promise<void>;
  deleteConversation: () => Promise<void>;
  getUserConversations: () => Promise<ConversationData[]>;
}

const PersistenceContext = createContext<PersistenceContextValue | null>(null);

/**
 * Provider component that adds automatic persistence capabilities to CopilotKit chat components
 * 
 * @example
 * ```tsx
 * import { CopilotKit } from "@copilotkit/react-core";
 * import { CopilotChat } from "@copilotkit/react-ui";
 * import { YaiNexusPersistenceProvider } from "@yai-nexus/fekit";
 * 
 * function ChatPage() {
 *   return (
 *     <CopilotKit url="/api/copilotkit">
 *       <YaiNexusPersistenceProvider
 *         userId="user_12345"
 *         conversationId="default-chat"
 *       >
 *         <CopilotChat />
 *       </YaiNexusPersistenceProvider>
 *     </CopilotKit>
 *   );
 * }
 * ```
 */
export function YaiNexusPersistenceProvider({
  userId,
  conversationId,
  children,
  autoSave = true,
  dbName,
}: YaiNexusPersistenceProviderProps) {
  const [storage, setStorage] = useState<ChatStorage | null>(null);
  const [conversation, setConversation] = useState<ConversationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize storage
  useEffect(() => {
    const initStorage = async () => {
      try {
        const chatStorage = new ChatStorage(dbName);
        await chatStorage.init();
        setStorage(chatStorage);
        
        // Load existing conversation
        const existingConversation = await chatStorage.loadConversation(conversationId);
        if (existingConversation) {
          setConversation(existingConversation);
        } else {
          // Create new conversation
          const newConversation: ConversationData = {
            id: conversationId,
            userId,
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          setConversation(newConversation);
          await chatStorage.saveConversation(newConversation);
        }
      } catch (error) {
        console.error('Failed to initialize chat storage:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initStorage();

    // Cleanup
    return () => {
      if (storage) {
        storage.close();
      }
    };
  }, [userId, conversationId, dbName]);

  const saveMessage = useCallback(async (
    messageData: Omit<ChatMessage, 'id' | 'conversationId' | 'timestamp'>
  ) => {
    if (!storage || !conversation) return;

    const message: ChatMessage = {
      ...messageData,
      id: ChatStorage.generateMessageId(),
      conversationId,
      timestamp: Date.now(),
    };

    try {
      await storage.addMessage(message);
      
      // Update local conversation state
      setConversation(prev => prev ? {
        ...prev,
        messages: [...prev.messages, message],
        updatedAt: message.timestamp,
      } : null);
    } catch (error) {
      console.error('Failed to save message:', error);
    }
  }, [storage, conversation, conversationId]);

  const loadConversation = useCallback(async () => {
    if (!storage) return;

    try {
      setIsLoading(true);
      const loadedConversation = await storage.loadConversation(conversationId);
      if (loadedConversation) {
        setConversation(loadedConversation);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    } finally {
      setIsLoading(false);
    }
  }, [storage, conversationId]);

  const clearConversation = useCallback(async () => {
    if (!storage || !conversation) return;

    try {
      // Clear messages but keep conversation
      const clearedConversation: ConversationData = {
        ...conversation,
        messages: [],
        updatedAt: Date.now(),
      };
      
      await storage.saveConversation(clearedConversation);
      setConversation(clearedConversation);
    } catch (error) {
      console.error('Failed to clear conversation:', error);
    }
  }, [storage, conversation]);

  const deleteConversation = useCallback(async () => {
    if (!storage) return;

    try {
      await storage.deleteConversation(conversationId);
      setConversation(null);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  }, [storage, conversationId]);

  const getUserConversations = useCallback(async () => {
    if (!storage) return [];

    try {
      return await storage.getUserConversations(userId);
    } catch (error) {
      console.error('Failed to get user conversations:', error);
      return [];
    }
  }, [storage, userId]);

  const contextValue: PersistenceContextValue = {
    storage,
    conversation,
    isLoading,
    saveMessage,
    loadConversation,
    clearConversation,
    deleteConversation,
    getUserConversations,
  };

  return (
    <PersistenceContext.Provider value={contextValue}>
      <PersistenceWrapper autoSave={autoSave}>
        {children}
      </PersistenceWrapper>
    </PersistenceContext.Provider>
  );
}

/**
 * Wrapper component that handles automatic message persistence
 */
function PersistenceWrapper({ children, autoSave }: { children: React.ReactNode; autoSave: boolean }) {
  const persistence = usePersistence();

  useEffect(() => {
    if (!autoSave || !persistence) return;

    // TODO: Integrate with CopilotKit's message events to auto-save messages
    // This would require hooking into CopilotKit's internal state management
    // For now, users need to manually call saveMessage when needed
    
  }, [autoSave, persistence]);

  return <>{children}</>;
}

/**
 * Hook to access persistence functionality
 */
export function usePersistence(): PersistenceContextValue | null {
  const context = useContext(PersistenceContext);
  return context;
}

/**
 * Hook to get the current conversation
 */
export function useConversation(): ConversationData | null {
  const persistence = usePersistence();
  return persistence?.conversation || null;
}

/**
 * Hook to save messages manually
 */
export function useSaveMessage() {
  const persistence = usePersistence();
  return persistence?.saveMessage || (async () => {});
}

/**
 * Hook to get conversation management functions
 */
export function useConversationManager() {
  const persistence = usePersistence();
  
  return {
    loadConversation: persistence?.loadConversation || (async () => {}),
    clearConversation: persistence?.clearConversation || (async () => {}),
    deleteConversation: persistence?.deleteConversation || (async () => {}),
    getUserConversations: persistence?.getUserConversations || (async () => []),
    isLoading: persistence?.isLoading || false,
  };
}