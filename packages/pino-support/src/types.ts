/**
 * Simplified types for pino-support
 */

export interface LoggerConfig {
  serviceName: string;
  level?: 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  console?: {
    enabled?: boolean;
    pretty?: boolean;
  };
  file?: {
    enabled?: boolean;
    path?: string; // simplified: just a file path
  };
}

/**
 * Environment detection result
 */
export interface EnvironmentInfo {
  /** Is running in browser environment */
  isBrowser: boolean;
  /** Is running in Node.js environment */
  isNode: boolean;
  /** Environment type for logging purposes */
  environment: 'browser' | 'node' | 'unknown';
}