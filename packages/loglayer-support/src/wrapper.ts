/**
 * LogLayer 包装器模块
 * 
 * 提供与现有 EnhancedLogger 兼容的接口包装
 */

import { LogLayer } from 'loglayer';
import type { IEnhancedLogger, LogMetadata } from './types';

/**
 * LogLayer 包装器类
 * 将 LogLayer 的 fluent API 适配为 EnhancedLogger 接口
 */
export class LogLayerWrapper implements IEnhancedLogger {
  private logLayer: LogLayer;
  private context: LogMetadata = {};

  constructor(logLayer: LogLayer, context: LogMetadata = {}) {
    this.logLayer = logLayer;
    this.context = context;
  }

  /**
   * 创建带有上下文的 LogLayer 实例
   */
  private withContext(additionalContext: LogMetadata = {}): LogLayer {
    const fullContext = { ...this.context, ...additionalContext };
    return Object.keys(fullContext).length > 0 
      ? this.logLayer.withContext(fullContext)
      : this.logLayer;
  }

  // 基础日志方法
  debug(message: string, metadata?: LogMetadata): void {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).debug(message);
    } else {
      logger.debug(message);
    }
  }

  info(message: string, metadata?: LogMetadata): void {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).info(message);
    } else {
      logger.info(message);
    }
  }

  warn(message: string, metadata?: LogMetadata): void {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).warn(message);
    } else {
      logger.warn(message);
    }
  }

  error(message: string, metadata?: LogMetadata): void {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).error(message);
    } else {
      logger.error(message);
    }
  }

  // 上下文绑定方法
  child(bindings: LogMetadata): IEnhancedLogger {
    const newContext = { ...this.context, ...bindings };
    return new LogLayerWrapper(this.logLayer, newContext);
  }

  forRequest(requestId: string, traceId?: string): IEnhancedLogger {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }

  forUser(userId: string): IEnhancedLogger {
    return this.child({ userId });
  }

  forModule(moduleName: string): IEnhancedLogger {
    return this.child({ module: moduleName });
  }

  // 增强方法
  logError(error: Error, context?: LogMetadata, message = "Error occurred"): void {
    const logger = this.withContext(context);
    logger
      .withError(error)
      .withMetadata({
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        ...context,
      })
      .error(message);
  }

  logPerformance(operation: string, duration: number, metadata?: LogMetadata): void {
    this.info("Performance metric", {
      performance: {
        operation,
        duration: `${duration}ms`,
        ...metadata,
      },
    });
  }

  // 原始 logger 访问
  get raw(): LogLayer {
    return this.logLayer;
  }
}

/**
 * 工具函数：生成请求 ID
 */
export function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * 工具函数：生成追踪 ID
 */
export function generateTraceId(): string {
  return `trace_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
}
