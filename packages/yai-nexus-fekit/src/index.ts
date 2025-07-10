/**
 * @fileoverview
 * This is the main entry point for the yai-nexus-fekit SDK.
 * It provides tools to connect CopilotKit frontend with yai-nexus-agentkit Python backend,
 * plus automatic chat persistence capabilities.
 */

// Core server-side functionality
export { createYaiNexusHandler } from './handler';
export type { CreateYaiNexusHandlerOptions, YaiNexusHandler } from './handler';

// Client-side persistence functionality
export { 
  YaiNexusPersistenceProvider,
  usePersistence,
  useConversation, 
  useSaveMessage,
  useConversationManager 
} from './provider';
export type { YaiNexusPersistenceProviderProps, PersistenceContextValue } from './provider';

// Storage functionality
export { ChatStorage } from './storage';
export type { ChatMessage, ConversationData } from './storage';

// Adapter (internal, but exported for advanced usage)
export { YaiNexusAdapter } from './adapter';
export type { YaiNexusAdapterConfig } from './adapter';

// Re-export protocol definitions and types from ag-ui
export * from "@ag-ui/proto"; 