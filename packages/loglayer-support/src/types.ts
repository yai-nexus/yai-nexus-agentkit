/**
 * 类型定义
 * 
 * 定义日志抽象层的核心类型和接口
 */

import type { LogLayer } from 'loglayer';

/**
 * 日志级别
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * 日志元数据
 */
export type LogMetadata = Record<string, unknown>;

/**
 * 兼容 EnhancedLogger 的接口
 */
export interface IEnhancedLogger {
  // 基础日志方法
  debug(message: string, metadata?: LogMetadata): void;
  info(message: string, metadata?: LogMetadata): void;
  warn(message: string, metadata?: LogMetadata): void;
  error(message: string, metadata?: LogMetadata): void;

  // 上下文绑定方法
  child(bindings: LogMetadata): IEnhancedLogger;
  forRequest(requestId: string, traceId?: string): IEnhancedLogger;
  forUser(userId: string): IEnhancedLogger;
  forModule(moduleName: string): IEnhancedLogger;

  // 增强方法
  logError(error: Error, context?: LogMetadata, message?: string): void;
  logPerformance(operation: string, duration: number, metadata?: LogMetadata): void;

  // 原始 logger 访问
  get raw(): LogLayer;
}

/**
 * 环境检测结果
 */
export interface EnvironmentInfo {
  isServer: boolean;
  isClient: boolean;
  isDevelopment: boolean;
  isProduction: boolean;
  isTest: boolean;
  environment: 'development' | 'production' | 'test';
  platform: 'node' | 'browser' | 'nextjs';
}

/**
 * 传输器配置选项
 */
export interface TransportOptions {
  // Pino 配置（服务器端高性能）
  pino?: {
    level?: string;
    streams?: Array<{
      stream: string | NodeJS.WritableStream;
      level?: string;
    }>;
    pretty?: boolean;
  };
  
  // Winston 配置（服务器端兼容性）
  winston?: {
    level?: string;
    format?: string;
    transports?: string[];
  };
  
  // Console 配置（开发环境）
  console?: {
    level?: string;
    pretty?: boolean;
  };
  
  // 简单终端配置（Next.js 兼容）
  simplePrettyTerminal?: {
    level?: string;
    colorize?: boolean;
  };
}

/**
 * 环境配置
 */
export interface EnvironmentConfig {
  // 首选传输器类型
  preferredTransport: 'pino' | 'winston' | 'console' | 'simplePrettyTerminal';
  
  // 备选传输器（兼容性问题时使用）
  fallbackTransport: 'winston' | 'console' | 'simplePrettyTerminal';
  
  // 传输器配置
  transportOptions: TransportOptions;
  
  // LogLayer 插件配置
  plugins?: Array<{
    name: string;
    config?: Record<string, unknown>;
  }>;
}

/**
 * 完整的日志配置
 */
export interface LoggerConfig {
  serviceName: string;
  
  // 环境配置映射
  environments: {
    development: {
      server: EnvironmentConfig;
      client: EnvironmentConfig;
    };
    production: {
      server: EnvironmentConfig;
      client: EnvironmentConfig;
    };
    test: {
      server: EnvironmentConfig;
      client: EnvironmentConfig;
    };
  };
  
  // 强制配置（用于解决特定兼容性问题）
  forceConfig?: {
    transport: 'winston' | 'console' | 'simplePrettyTerminal';
    reason?: string; // 强制使用的原因，如 "Next.js pino compatibility issue"
  };
}
