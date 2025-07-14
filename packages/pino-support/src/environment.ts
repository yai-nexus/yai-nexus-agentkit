/**
 * Simplified environment detection
 */

import { EnvironmentInfo } from './types';

/**
 * Detect current runtime environment
 */
export function detectEnvironment(): EnvironmentInfo {
  const isBrowser = typeof globalThis !== 'undefined' && typeof (globalThis as any).window !== 'undefined' && typeof (globalThis as any).window.document !== 'undefined';
  const isNode = typeof process !== 'undefined' && process.versions != null && process.versions.node != null;
  
  return {
    isBrowser,
    isNode,
    environment: isBrowser ? 'browser' : isNode ? 'node' : 'unknown'
  };
}

/**
 * Check if file operations are supported
 */
export function supportsFileOperations(): boolean {
  return detectEnvironment().isNode;
}