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
  useConversationManager 
} from './provider';
export type { YaiNexusPersistenceProviderProps } from './provider';

// Storage functionality
export { ChatStorage } from './storage';
export type { ChatMessage, ConversationData } from './storage';

// Note: YaiNexusAdapter has been removed in favor of direct AG-UI integration
// Users should now use the agents configuration in CopilotRuntime 