/**
 * Enhanced pino-support with directory strategy support
 */

import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import pino from "pino";
import { detectEnvironment, supportsFileOperations } from "./environment";
import {
  DailyDirectoryStrategy,
  DirectoryStrategy,
  HourlyDirectoryStrategy,
  SimpleFileStrategy,
} from "./strategies";
import { LoggerConfig } from "./types";

// 导出策略类和接口
export {
  DailyDirectoryStrategy,
  HourlyDirectoryStrategy,
  SimpleFileStrategy,
} from "./strategies";

// 导出类型
export type { DirectoryStrategy } from "./strategies";
export type { LoggerConfig } from "./types";

/**
 * 创建目录策略实例
 */
function createDirectoryStrategy(
  config: LoggerConfig
): DirectoryStrategy | null {
  if (!config.file?.enabled) {
    return null;
  }

  const fileConfig = config.file;
  const baseDir = fileConfig.baseDir || "logs";

  // 如果指定了具体的 path，使用简单文件策略
  if (fileConfig.path) {
    return new SimpleFileStrategy({
      baseDir: path.dirname(fileConfig.path),
      filename: path.basename(fileConfig.path),
    });
  }

  // 根据策略类型创建相应的策略实例
  if (typeof fileConfig.strategy === "object") {
    // 直接传入的策略实例
    return fileConfig.strategy;
  }

  switch (fileConfig.strategy) {
    case "hourly":
      return new HourlyDirectoryStrategy({ baseDir });
    case "daily":
      return new DailyDirectoryStrategy({ baseDir });
    case "simple":
    default:
      return new SimpleFileStrategy({ baseDir });
  }
}

/**
 * Create an enhanced pino logger with directory strategy support
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

  // File stream (Node.js only) - enhanced with directory strategy support
  if (config.file?.enabled && supportsFileOperations()) {
    const strategy = createDirectoryStrategy(config);

    if (strategy) {
      try {
        // 使用策略生成日志文件路径
        const filePath = strategy.getLogPath(config.serviceName);

        // 确保目录存在（策略已经处理了目录创建）
        const dir = path.dirname(filePath);
        fs.mkdirSync(dir, { recursive: true });

        // 创建文件流
        const fileStream = fs.createWriteStream(filePath, { flags: "a" });

        // 应用美化格式（如果请求）
        if (config.file.pretty) {
          try {
            const { default: pretty } = await import("pino-pretty");

            // 使用 pino-pretty 输出到文件
            streams.push({
              stream: pretty({
                destination: filePath,
                colorize: false,
                translateTime: "SYS:yyyy-mm-dd HH:MM:ss",
                ignore: "pid,hostname",
                sync: true,
              }),
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
  }

  // Return logger
  if (streams.length === 0) {
    return pino(pinoOptions);
  } else {
    return pino(pinoOptions, pino.multistream(streams));
  }
}

/**
 * 统一配置函数 - 与 loguru-support 语义一致
 */
export async function setupLogging(
  serviceName: string,
  config: Partial<LoggerConfig> = {}
): Promise<pino.Logger> {
  const defaultConfig: LoggerConfig = {
    serviceName,
    level: "info",
    console: {
      enabled: true,
      pretty: process.env.NODE_ENV !== "production",
    },
    file: {
      enabled: true,
      strategy: "hourly",
      baseDir: "logs",
      pretty: false,
    },
  };

  // 合并配置
  const mergedConfig = {
    ...defaultConfig,
    ...config,
    console: { ...defaultConfig.console, ...config.console },
    file: { ...defaultConfig.file, ...config.file },
    cloud: { ...defaultConfig.cloud, ...config.cloud },
  };

  return createLogger(mergedConfig);
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
    file: { enabled: true, pretty: true, strategy: "hourly" },
  });
}

export async function createProdLogger(
  serviceName: string
): Promise<pino.Logger> {
  return createLogger({
    serviceName,
    level: "info",
    console: { enabled: true, pretty: false },
    file: { enabled: true, pretty: false, strategy: "hourly" },
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
