/**
 * 增强的 Logger 类 - 提供便捷方法和类型安全
 * 
 * 从 Next.js 应用中提取的通用 Logger 功能，
 * 可以在任何使用 pino-support 的项目中复用
 */

import pino from "pino";

export class EnhancedLogger {
  private pino: pino.Logger;

  constructor(pinoInstance: pino.Logger) {
    this.pino = pinoInstance;
  }

  /**
   * 创建子记录器，继承当前上下文并添加新的绑定字段
   */
  child(bindings: Record<string, unknown>): EnhancedLogger {
    return new EnhancedLogger(this.pino.child(bindings));
  }

  /**
   * 为请求创建专门的子记录器
   */
  forRequest(requestId: string, traceId?: string): EnhancedLogger {
    const bindings: Record<string, unknown> = { requestId };
    if (traceId) {
      bindings.traceId = traceId;
    }
    return this.child(bindings);
  }

  /**
   * 为用户操作创建子记录器
   */
  forUser(userId: string): EnhancedLogger {
    return this.child({ userId });
  }

  /**
   * 为特定模块创建子记录器
   */
  forModule(moduleName: string): EnhancedLogger {
    return this.child({ module: moduleName });
  }

  // 标准日志方法
  trace(message: string, obj?: object): void;
  trace(obj: object, message?: string): void;
  trace(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.trace(objOrMsg as object, msgOrObj);
    } else {
      this.pino.trace(msgOrObj, objOrMsg as string);
    }
  }

  debug(message: string, obj?: object): void;
  debug(obj: object, message?: string): void;
  debug(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.debug(objOrMsg as object, msgOrObj);
    } else {
      this.pino.debug(msgOrObj, objOrMsg as string);
    }
  }

  info(message: string, obj?: object): void;
  info(obj: object, message?: string): void;
  info(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.info(objOrMsg as object, msgOrObj);
    } else {
      this.pino.info(msgOrObj, objOrMsg as string);
    }
  }

  warn(message: string, obj?: object): void;
  warn(obj: object, message?: string): void;
  warn(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.warn(objOrMsg as object, msgOrObj);
    } else {
      this.pino.warn(msgOrObj, objOrMsg as string);
    }
  }

  error(message: string, obj?: object): void;
  error(obj: object, message?: string): void;
  error(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.error(objOrMsg as object, msgOrObj);
    } else {
      this.pino.error(msgOrObj, objOrMsg as string);
    }
  }

  fatal(message: string, obj?: object): void;
  fatal(obj: object, message?: string): void;
  fatal(msgOrObj: string | object, objOrMsg?: object | string): void {
    if (typeof msgOrObj === "string") {
      this.pino.fatal(objOrMsg as object, msgOrObj);
    } else {
      this.pino.fatal(msgOrObj, objOrMsg as string);
    }
  }

  /**
   * 记录HTTP请求相关信息
   */
  logRequest(
    req: {
      method?: string;
      url?: string;
      headers?: Record<string, unknown>;
      body?: unknown;
    },
    message = "HTTP Request"
  ): void {
    this.info(message, {
      http: {
        method: req.method,
        url: req.url,
        userAgent: req.headers?.["user-agent"],
        contentType: req.headers?.["content-type"],
      },
    });
  }

  /**
   * 记录HTTP响应相关信息
   */
  logResponse(
    res: {
      status?: number;
      statusText?: string;
      headers?: Record<string, unknown>;
    },
    duration?: number,
    message = "HTTP Response"
  ): void {
    this.info(message, {
      http: {
        status: res.status,
        statusText: res.statusText,
      },
      ...(duration && { duration: `${duration}ms` }),
    });
  }

  /**
   * 记录错误信息，自动提取错误详情
   */
  logError(
    error: Error,
    context?: Record<string, unknown>,
    message = "Error occurred"
  ): void {
    this.error(message, {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
      },
      ...context,
    });
  }

  /**
   * 记录性能指标
   */
  logPerformance(
    operation: string,
    duration: number,
    metadata?: Record<string, unknown>
  ): void {
    this.info("Performance metric", {
      performance: {
        operation,
        duration: `${duration}ms`,
        ...metadata,
      },
    });
  }

  /**
   * 获取原始 pino logger（用于高级用法）
   */
  get raw(): pino.Logger {
    return this.pino;
  }
}

/**
 * 便捷函数：生成请求 ID
 */
export function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
}

/**
 * 便捷函数：生成追踪 ID
 */
export function generateTraceId(): string {
  return `trace_${Date.now()}_${Math.random().toString(36).substring(2, 14)}`;
}
