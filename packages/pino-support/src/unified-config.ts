/**
 * Unified logging configuration for pino
 * 
 * Provides isomorphic logger configuration that works across browser, Node.js,
 * and Next.js environments. Configuration interface matches the TypeScript
 * LoggerConfig interface defined in types.ts.
 */

import pino from 'pino';
import { detectEnvironment, supportsFileOperations, getEnvironmentDefaults } from './environment';
import { createFileTransport, FileTransportOptions } from './transports/file-transport';
import { LoggerConfig } from './types';

// Default configuration that matches loguru-support semantics
const DEFAULT_CONFIG: Partial<LoggerConfig> = {
  level: 'info',
  console: {
    enabled: true,
    pretty: true
  },
  file: {
    enabled: true,
    baseDir: 'logs',
    strategy: 'hourly',
    maxSize: undefined,
    maxFiles: undefined
  },
  cloud: {
    enabled: false,
    sls: undefined
  }
};

/**
 * Create a configured pino logger instance
 * 
 * This function is isomorphic and will automatically detect the runtime environment
 * to provide appropriate transport configurations. In browser environments, file
 * logging is automatically disabled.
 * 
 * @param config Logger configuration object
 * @returns Configured pino logger instance
 * 
 * @example
 * ```typescript
 * // Basic usage with defaults
 * const logger = createLogger({ serviceName: 'my-service' });
 * 
 * // Custom configuration
 * const logger = createLogger({
 *   serviceName: 'my-service',
 *   level: 'debug',
 *   console: { enabled: true, pretty: false },
 *   file: { enabled: true, strategy: 'daily' }
 * });
 * 
 * // Browser-safe configuration (file logging auto-disabled)
 * const logger = createLogger({ serviceName: 'my-app' }); // Works in both Node.js and browser
 * ```
 */
export function createLogger(config: LoggerConfig): pino.Logger {
  const env = detectEnvironment();
  const envDefaults = getEnvironmentDefaults();
  
  // Merge configuration with environment-aware defaults
  const finalConfig = mergeConfig(DEFAULT_CONFIG, envDefaults, config);
  
  // Validate service name
  if (!finalConfig.serviceName) {
    throw new Error('serviceName is required in logger configuration');
  }
  
  // Build pino options
  const pinoOptions: pino.LoggerOptions = {
    level: finalConfig.level || 'info',
    timestamp: pino.stdTimeFunctions.isoTime,
    // Add service name to every log entry
    base: {
      service: finalConfig.serviceName,
      environment: env.environment,
      isNextJs: env.isNextJs
    }
  };
  
  // Determine transports based on environment and configuration
  const transports: any[] = [];
  
  // Console transport
  if (finalConfig.console?.enabled) {
    if (env.isBrowser) {
      // Browser console transport
      transports.push({
        target: 'pino/browser',
        options: {
          write: (obj: any) => {
            // Use browser console with appropriate method based on level
            const level = obj.level;
            const method = level >= 50 ? 'error' : level >= 40 ? 'warn' : level >= 30 ? 'info' : 'log';
            console[method](obj);
          }
        }
      });
    } else {
      // Node.js console transport
      if (finalConfig.console?.pretty && process.env.NODE_ENV !== 'production') {
        transports.push({
          target: 'pino-pretty',
          options: {
            colorize: true,
            translateTime: 'yyyy-mm-dd HH:MM:ss.l',
            ignore: 'pid,hostname',
            messageFormat: '{service} [{level}] {msg}'
          }
        });
      } else {
        // JSON console output for production
        transports.push({
          target: 'pino/file',
          options: {
            destination: 1 // stdout
          }
        });
      }
    }
  }
  
  // File transport (only in Node.js environment)
  if (finalConfig.file?.enabled && supportsFileOperations()) {
    const fileOptions: FileTransportOptions = {
      serviceName: finalConfig.serviceName,
      baseDir: finalConfig.file.baseDir || 'logs',
      strategy: finalConfig.file.strategy || 'hourly',
      createSymlink: true,
      createReadme: true,
      maxSize: finalConfig.file.maxSize,
      maxFiles: finalConfig.file.maxFiles
    };
    
    transports.push({
      target: 'pino-abstract-transport',
      options: {},
      // Custom transport factory
      transport: createFileTransport(fileOptions)
    });
  }
  
  // Create logger with transports
  let logger: pino.Logger;
  
  if (transports.length === 0) {
    // Fallback to basic logger if no transports
    logger = pino(pinoOptions);
  } else if (transports.length === 1) {
    // Single transport
    logger = pino(pinoOptions, transports[0].transport || pino.destination(transports[0]));
  } else {
    // Multiple transports
    logger = pino(pinoOptions, pino.multistream(transports));
  }
  
  return logger;
}

/**
 * Deep merge configuration objects
 */
function mergeConfig(...configs: Array<Partial<LoggerConfig>>): LoggerConfig {
  const result: any = {};
  
  for (const config of configs) {
    for (const [key, value] of Object.entries(config)) {
      if (value !== undefined) {
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          result[key] = mergeConfig(result[key] || {}, value);
        } else {
          result[key] = value;
        }
      }
    }
  }
  
  return result as LoggerConfig;
}

/**
 * Get logger metadata for debugging and monitoring
 * 
 * @param logger Pino logger instance
 * @returns Metadata object with logger information
 */
export function getLoggerMetadata(logger: pino.Logger): Record<string, any> {
  const env = detectEnvironment();
  
  return {
    package_name: '@yai-nexus/pino-support',
    logger_type: 'pino',
    environment: env.environment,
    is_browser: env.isBrowser,
    is_node: env.isNode,
    is_nextjs: env.isNextJs,
    supports_file_ops: supportsFileOperations(),
    level: logger.level,
    service: (logger as any).bindings?.()?.service || 'unknown'
  };
}

/**
 * Convenience functions for common configurations
 */

/**
 * Development environment logger with pretty console output and file logging
 */
export function createDevLogger(serviceName: string): pino.Logger {
  return createLogger({
    serviceName,
    level: 'debug',
    console: { enabled: true, pretty: true },
    file: { enabled: true, strategy: 'hourly' }
  });
}

/**
 * Production environment logger with JSON output and structured file logging
 */
export function createProdLogger(serviceName: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info'): pino.Logger {
  return createLogger({
    serviceName,
    level,
    console: { enabled: true, pretty: false },
    file: { enabled: true, strategy: 'hourly' }
  });
}

/**
 * Console-only logger for CI/CD or containerized environments
 */
export function createConsoleLogger(serviceName: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info'): pino.Logger {
  return createLogger({
    serviceName,
    level,
    console: { enabled: true, pretty: false },
    file: { enabled: false }
  });
}

/**
 * Browser-optimized logger that gracefully handles client-side logging
 */
export function createBrowserLogger(serviceName: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info'): pino.Logger {
  return createLogger({
    serviceName,
    level,
    console: { enabled: true, pretty: true },
    file: { enabled: false } // Always disabled in browser
  });
}