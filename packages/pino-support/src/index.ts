/**
 * Simplified pino-support - using community components
 */

import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import pino from "pino";
import { detectEnvironment, supportsFileOperations } from "./environment";
import { LoggerConfig } from "./types";

/**
 * Create a simplified pino logger
 */
export async function createLogger(config: LoggerConfig): Promise<pino.Logger> {
  const env = detectEnvironment();

  // Validate service name
  if (!config.serviceName) {
    throw new Error("serviceName is required");
  }

  // Build pino options
  const pinoOptions: pino.LoggerOptions = {
    level: config.level || "info",
    base: {
      service: config.serviceName,
      environment: env.environment,
    },
  };

  // Build streams
  const streams: any[] = [];

  // Console stream
  if (config.console?.enabled !== false) {
    if (env.isBrowser) {
      // Browser: use console
      streams.push({
        stream: { write: (msg: string) => console.log(msg) },
      });
    } else {
      // Node.js: use stdout with optional pretty printing
      if (config.console?.pretty && process.env.NODE_ENV !== "production") {
        try {
          const { default: pretty } = await import("pino-pretty");
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
      const fileStream = fs.createWriteStream(filePath, { flags: "a" });

      // Apply pretty formatting if requested
      if (config.file.pretty) {
        try {
          const { default: pretty } = await import("pino-pretty");
          
          // 最简单的方式：直接用 pino-pretty，让它输出到文件
          streams.push({ 
            stream: pretty({
              destination: filePath,
              colorize: false,
              translateTime: "SYS:yyyy-mm-dd HH:MM:ss",
              ignore: "pid,hostname",
              sync: true,
            })
          });
        } catch (error) {
          // Fallback to JSON format if pino-pretty fails
          console.warn("pino-pretty error for file output:", error);
          streams.push({ stream: fileStream });
        }
      } else {
        // Default JSON format
        streams.push({ stream: fileStream });
      }
    } catch (error: any) {
      console.warn("File logging failed:", error?.message || "Unknown error");
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
export async function createDevLogger(
  serviceName: string
): Promise<pino.Logger> {
  return createLogger({
    serviceName,
    level: "debug",
    console: { enabled: true, pretty: true },
    file: { enabled: true, pretty: true },
  });
}

export async function createProdLogger(
  serviceName: string
): Promise<pino.Logger> {
  return createLogger({
    serviceName,
    level: "info",
    console: { enabled: true, pretty: false },
    file: { enabled: true, pretty: false },
  });
}

export async function createConsoleLogger(
  serviceName: string
): Promise<pino.Logger> {
  return createLogger({
    serviceName,
    level: "info",
    console: { enabled: true, pretty: false },
    file: { enabled: false },
  });
}

// Re-export environment detection
export { detectEnvironment, supportsFileOperations } from "./environment";

// Re-export types
export * from "./types";

// Metadata function
export function getLoggerMetadata(
  _logger: pino.Logger
): Record<string, unknown> {
  return {
    version: "0.2.6", // Static version to avoid require()
    pid: process.pid,
    hostname: os.hostname(),
    timestamp: new Date().toISOString(),
  };
}
