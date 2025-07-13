/**
 * Environment detection utilities for isomorphic logger setup
 */

import { EnvironmentInfo } from './types';

/**
 * Detect the current runtime environment with enhanced Next.js support
 * 
 * Uses multiple detection methods to handle edge cases like SSR hydration
 * and build-time vs runtime differences.
 * 
 * @returns EnvironmentInfo object describing the current environment
 */
export function detectEnvironment(): EnvironmentInfo {
  // Check for browser environment
  const isBrowser = typeof window !== 'undefined' && typeof window.document !== 'undefined';
  
  // Check for Node.js environment with additional safety checks
  const isNode = typeof process !== 'undefined' && 
                 process.versions != null && 
                 process.versions.node != null;
  
  // Detect Next.js environment
  // Check for Next.js specific globals and environment variables
  const isNextJs = (
    // Next.js sets this during build and runtime
    typeof process !== 'undefined' && process.env.__NEXT_PRIVATE_PREBUNDLED_REACT != null
  ) || (
    // Next.js router and other globals
    typeof window !== 'undefined' && (window as any).__NEXT_DATA__ != null
  ) || (
    // Check for Next.js specific process.env flags
    typeof process !== 'undefined' && process.env.NODE_ENV != null && 
    (process.env.NEXT_RUNTIME != null || process.env.__NEXT_ROUTER_BASEPATH != null)
  );
  
  // Additional environment checks for edge cases
  let environment: 'browser' | 'node' | 'unknown';
  
  if (isBrowser) {
    environment = 'browser';
  } else if (isNode) {
    environment = 'node';
  } else {
    environment = 'unknown';
  }
  
  return {
    isBrowser,
    isNode,
    isNextJs,
    environment
  };
}

/**
 * Check if file operations are supported in the current environment
 * 
 * @returns true if file operations are available and safe to use
 */
export function supportsFileOperations(): boolean {
  const env = detectEnvironment();
  
  // File operations are only safe in Node.js environment
  return env.isNode && !env.isBrowser;
}

/**
 * Get environment-specific logger configuration defaults
 * 
 * @returns configuration object suitable for the current environment
 */
export function getEnvironmentDefaults() {
  const env = detectEnvironment();
  
  if (env.isBrowser) {
    return {
      console: { enabled: true, pretty: true },
      file: { enabled: false }, // Files not supported in browser
      transports: ['console']
    };
  } else if (env.isNode) {
    return {
      console: { enabled: true, pretty: process.env.NODE_ENV !== 'production' },
      file: { enabled: true },
      transports: ['console', 'file']
    };
  } else {
    return {
      console: { enabled: true, pretty: false },
      file: { enabled: false },
      transports: ['console']
    };
  }
}