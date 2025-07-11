/**
 * @fileoverview
 * Client-side entry point for yai-nexus-fekit SDK.
 * This module exports components and utilities that are safe to use in the browser.
 */

"use client";

// Client-side persistence functionality
export { 
  YaiNexusPersistenceProvider,
  useConversationManager 
} from './provider';
export type { YaiNexusPersistenceProviderProps } from './provider';

// Storage functionality (browser-safe)
export { ChatStorage } from './storage';
export type { ChatMessage, ConversationData } from './storage'; 