/**
 * Simplified pino-support - using community components
 */

import pino from 'pino';
import { LoggerConfig } from './types';
import { detectEnvironment, supportsFileOperations } from './environment';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Create a simplified pino logger
 */
export function createLogger(config: LoggerConfig): pino.Logger {
  const env = detectEnvironment();
  
  // Validate service name
  if (!config.serviceName) {
    throw new Error('serviceName is required');
  }
  
  // Build pino options
  const pinoOptions: pino.LoggerOptions = {
    level: config.level || 'info',
    base: {
      service: config.serviceName,
      environment: env.environment
    }
  };

  // Build streams
  const streams: any[] = [];
  
  // Console stream
  if (config.console?.enabled !== false) {
    if (env.isBrowser) {
      // Browser: use console
      streams.push({ 
        stream: { write: (msg: string) => console.log(msg) }
      });
    } else {
      // Node.js: use stdout with optional pretty printing
      if (config.console?.pretty && process.env.NODE_ENV !== 'production') {
        try {
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
  
  // File stream (Node.js only) - simplified file output
  if (config.file?.enabled && supportsFileOperations()) {
    const filePath = config.file.path || `logs/${config.serviceName}.log`;
    try {
      // Ensure directory exists
      const dir = path.dirname(filePath);
      fs.mkdirSync(dir, { recursive: true });
      
      // Create file stream
      const fileStream = fs.createWriteStream(filePath, { flags: 'a' });
      
      // Apply pretty formatting if requested
      if (config.file.pretty) {
        try {
          const pretty = require('pino-pretty');
          // Create a transform stream that will format the output
          const prettyTransform = pretty({
            colorize: false,
            translateTime: 'SYS:yyyy-mm-dd HH:MM:ss',
            ignore: 'pid,hostname',
            sync: true
          });
          
          // Create a custom stream that pipes through pretty formatter
          streams.push({
            stream: {
              write: (chunk: any) => {
                try {
                  const formatted = prettyTransform(JSON.parse(chunk));
                  fileStream.write(formatted + '\n');
                } catch (err) {
                  // Fallback to raw JSON if formatting fails
                  fileStream.write(chunk);
                }
              }
            }
          });
        } catch (error) {
          // Fallback to JSON format if pino-pretty fails
          console.warn('pino-pretty error for file output:', error);
          streams.push({ stream: fileStream });
        }
      } else {
        // Default JSON format
        streams.push({ stream: fileStream });
      }
    } catch (error: any) {
      console.warn('File logging failed:', error?.message || 'Unknown error');
    }
  }
  
  // Return logger
  if (streams.length === 0) {
    return pino(pinoOptions);
  } else {
    return pino(pinoOptions, pino.multistream(streams));
  }
}

/**
 * Convenience functions
 */
export function createDevLogger(serviceName: string): pino.Logger {
  return createLogger({
    serviceName,
    level: 'debug',
    console: { enabled: true, pretty: true },
    file: { enabled: true, pretty: true }
  });
}

export function createProdLogger(serviceName: string): pino.Logger {
  return createLogger({
    serviceName,
    level: 'info',
    console: { enabled: true, pretty: false },
    file: { enabled: true, pretty: false }
  });
}

export function createConsoleLogger(serviceName: string): pino.Logger {
  return createLogger({
    serviceName,
    level: 'info',
    console: { enabled: true, pretty: false },
    file: { enabled: false }
  });
}

// Re-export environment detection
export { detectEnvironment, supportsFileOperations } from './environment';

// Re-export types
export * from './types';

// Metadata function
export function getLoggerMetadata(logger: pino.Logger): Record<string, unknown> {
  return {
    version: require('../package.json').version || 'unknown',
    pid: process.pid,
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  };
}