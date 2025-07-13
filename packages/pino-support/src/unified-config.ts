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
import { createSlsTransportConfig } from './transports/sls-transport';
import { LoggerConfig } from './types';
import { join } from 'path';
import { existsSync } from 'fs';
import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { findMonorepoRoot } from './utils';
// 直接用 pino.multistream，无需单独依赖

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

  // 多路输出流数组
  const streams: any[] = [];

  // 文件流
  if (finalConfig.file?.enabled && supportsFileOperations()) {
    const fileTransportOptions: FileTransportOptions = {
      baseDir: finalConfig.file.baseDir || 'logs',
      strategy: finalConfig.file.strategy || 'hourly',
      serviceName: finalConfig.serviceName,
      createSymlink: true,
      createReadme: true,
      maxSize: finalConfig.file.maxSize,
      maxFiles: finalConfig.file.maxFiles,
      projectRoot: findMonorepoRoot(),
    };
    const fileTransport = createFileTransport(fileTransportOptions);
    streams.push({ stream: fileTransport });
  }

  // 控制台流
  if (finalConfig.console?.enabled) {
    if (env.isBrowser) {
      // 浏览器环境下，直接用 console
      streams.push({ stream: { write: (msg: string) => console.log(msg) } });
    } else {
      if (finalConfig.console?.pretty && process.env.NODE_ENV !== 'production') {
        // 用 pino-pretty 美化
        try {
          // 动态引入 pino-pretty，避免依赖问题
          // eslint-disable-next-line @typescript-eslint/no-var-requires
          const pretty = require('pino-pretty');
          streams.push({ stream: pretty() });
        } catch {
          streams.push({ stream: process.stdout });
        }
      } else {
        streams.push({ stream: process.stdout });
      }
    }
  }

  // SLS 云日志流
  if (finalConfig.cloud?.enabled && finalConfig.cloud.sls && supportsFileOperations()) {
    try {
      // 动态引入 SLS transport
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const { createSlsTransport } = require('./transports/sls-transport');
      const slsStream = createSlsTransport(finalConfig.cloud.sls);
      streams.push({ stream: slsStream });
    } catch {
      console.warn('SLS cloud logging is configured but not yet implemented or missing dependency');
    }
  }

  // 如果没有任何流，降级为默认 logger
  if (streams.length === 0) {
    return pino(pinoOptions);
  }

  // 多路输出
  return pino(pinoOptions, pino.multistream(streams));
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
          result[key] = mergeConfig(result[key] || {}, value as Partial<LoggerConfig>);
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