"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { useCopilotChat } from '@copilotkit/react-core';
import { ChatStorage, ChatMessage, ConversationData } from './storage';
import { Message, TextMessage } from '@copilotkit/runtime-client-gql';

export interface YaiNexusPersistenceProviderProps {
  userId: string;
  conversationId: string;
  children: React.ReactNode;
  autoSave?: boolean;
  dbName?: string;
}

// Removed PersistenceContext as we're now syncing directly with CopilotKit

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
  return (
    <PersistenceSync
      userId={userId}
      conversationId={conversationId}
      autoSave={autoSave}
      dbName={dbName}
    >
      {children}
    </PersistenceSync>
  );
}

/**
 * Sync component that handles automatic message persistence with CopilotKit
 */
function PersistenceSync({ 
  userId, 
  conversationId, 
  autoSave, 
  dbName,
  children 
}: YaiNexusPersistenceProviderProps) {
  const { visibleMessages, appendMessage, setMessages } = useCopilotChat({});
  const [storage, setStorage] = useState<ChatStorage | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [lastMessageCount, setLastMessageCount] = useState(0);

  // Initialize storage
  useEffect(() => {
    const initStorage = async () => {
      try {
        const chatStorage = new ChatStorage(dbName);
        await chatStorage.init();
        setStorage(chatStorage);
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize chat storage:', error);
      }
    };

    initStorage();

    return () => {
      if (storage) {
        storage.close();
      }
    };
  }, [dbName]);

  // Load conversation history on mount
  useEffect(() => {
    if (!storage || !isInitialized) return;

    const loadHistory = async () => {
      try {
        const existingConversation = await storage.loadConversation(conversationId);
        if (existingConversation && existingConversation.messages.length > 0) {
          // Convert stored messages to CopilotKit format and inject them
          const copilotMessages: Message[] = existingConversation.messages.map((msg: any) => 
            new TextMessage({
              id: msg.id,
              role: msg.role,
              content: msg.content,
              createdAt: new Date(msg.timestamp).toISOString(),
            })
          );
          
          // Inject messages into CopilotKit by setting them
          setMessages(copilotMessages);
          
          setLastMessageCount(copilotMessages.length);
        }
      } catch (error) {
        console.error('Failed to load conversation history:', error);
      }
    };

    loadHistory();
  }, [storage, isInitialized, conversationId, setMessages]);

  // Auto-save new messages
  useEffect(() => {
    if (!storage || !autoSave || !isInitialized) return;
    if (visibleMessages.length <= lastMessageCount) return;

    const saveNewMessages = async () => {
      try {
        // Get new messages
        const newMessages = visibleMessages.slice(lastMessageCount);
        
        for (const message of newMessages) {
          if (message.isTextMessage()) {
            const chatMessage: ChatMessage = {
              id: message.id,
              conversationId,
              role: message.role as 'user' | 'assistant' | 'system',
              content: message.content,
              timestamp: new Date(message.createdAt).getTime(),
            };
            
            await storage.addMessage(chatMessage);
          }
        }
        
        // Update conversation metadata
        const conversation: ConversationData = {
          id: conversationId,
          userId,
          messages: visibleMessages
            .filter((msg) => msg.isTextMessage())
            .map((msg) => ({
              id: msg.id,
              conversationId,
              role: (msg as TextMessage).role as 'user' | 'assistant' | 'system',
              content: (msg as TextMessage).content,
              timestamp: new Date(msg.createdAt).getTime(),
            })),
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        
        await storage.saveConversation(conversation);
        setLastMessageCount(visibleMessages.length);
      } catch (error) {
        console.error('Failed to save new messages:', error);
      }
    };

    saveNewMessages();
  }, [visibleMessages, storage, autoSave, isInitialized, lastMessageCount, conversationId, userId]);

  return <>{children}</>;
}

/**
 * Hook to get conversation management functions
 * Note: These are utility functions that work directly with storage
 */
export function useConversationManager(userId?: string, dbName?: string) {
  const [storage, setStorage] = useState<ChatStorage | null>(null);
  
  useEffect(() => {
    const initStorage = async () => {
      try {
        const chatStorage = new ChatStorage(dbName);
        await chatStorage.init();
        setStorage(chatStorage);
      } catch (error) {
        console.error('Failed to initialize storage for conversation manager:', error);
      }
    };
    
    initStorage();
    
    return () => {
      if (storage) {
        storage.close();
      }
    };
  }, [dbName]);
  
  const clearConversation = useCallback(async (conversationId: string) => {
    if (!storage) return;
    
    try {
      const conversation = await storage.loadConversation(conversationId);
      if (conversation) {
        const clearedConversation: ConversationData = {
          ...conversation,
          messages: [],
          updatedAt: Date.now(),
        };
        await storage.saveConversation(clearedConversation);
      }
    } catch (error) {
      console.error('Failed to clear conversation:', error);
    }
  }, [storage]);
  
  const deleteConversation = useCallback(async (conversationId: string) => {
    if (!storage) return;
    
    try {
      await storage.deleteConversation(conversationId);
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  }, [storage]);
  
  const getUserConversations = useCallback(async (): Promise<ConversationData[]> => {
    if (!storage || !userId) return [];
    
    try {
      return await storage.getUserConversations(userId);
    } catch (error) {
      console.error('Failed to get user conversations:', error);
      return [];
    }
  }, [storage, userId]);
  
  return {
    clearConversation,
    deleteConversation,
    getUserConversations,
    isStorageReady: !!storage,
  };
}