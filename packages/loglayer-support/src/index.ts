/**
 * @yai-nexus/loglayer-support 主入口
 *
 * 提供便捷的 API 来创建和配置基于 LogLayer 的日志系统
 */

// 导出所有类型
export type * from "./types";

// 导出核心模块
export * from "./config";
export * from "./environment";
export * from "./factory";
export * from "./presets";
export * from "./transports";
export * from "./wrapper";

// 导入核心功能
import { detectEnvironment } from "./environment";
import { LogLayerFactory } from "./factory";
import { presets } from "./presets";
import type { EnvironmentInfo, IEnhancedLogger, LoggerConfig } from "./types";
import { generateRequestId, generateTraceId } from "./wrapper";

/**
 * 全局 logger 实例管理
 */
let globalLogger: IEnhancedLogger | null = null;
let initPromise: Promise<IEnhancedLogger> | null = null;

/**
 * 创建增强的 Logger 实例
 *
 * @param config Logger 配置
 * @param env 环境信息（可选，自动检测）
 * @returns Promise<IEnhancedLogger>
 */
export async function createEnhancedLogger(
  config: LoggerConfig,
  env?: EnvironmentInfo
): Promise<IEnhancedLogger> {
  const environment = env || detectEnvironment();
  return LogLayerFactory.createValidatedLogger(config, environment);
}

/**
 * 便捷函数：使用预设创建 Logger
 *
 * @param serviceName 服务名称
 * @param preset 预设名称
 * @returns Promise<IEnhancedLogger>
 */
export async function createLoggerWithPreset(
  serviceName: string,
  preset: keyof typeof presets = "development"
): Promise<IEnhancedLogger> {
  const config = presets[preset](serviceName);
  return createEnhancedLogger(config);
}

/**
 * 初始化全局 Logger
 *
 * @param config Logger 配置
 * @returns Promise<IEnhancedLogger>
 */
export async function initGlobalLogger(
  config: LoggerConfig
): Promise<IEnhancedLogger> {
  if (globalLogger) return globalLogger;

  if (initPromise) return initPromise;

  initPromise = createEnhancedLogger(config);
  globalLogger = await initPromise;

  return globalLogger;
}

/**
 * 获取全局 Logger 实例
 * 如果未初始化，会使用默认配置自动初始化
 *
 * @param serviceName 服务名称（仅在首次初始化时使用）
 * @returns Promise<IEnhancedLogger>
 */
export async function getGlobalLogger(
  serviceName = "default-service"
): Promise<IEnhancedLogger> {
  if (globalLogger) return globalLogger;

  // 使用默认配置初始化
  const env = detectEnvironment();
  const preset = env.platform === "nextjs" ? "nextjsCompatible" : "development";
  const config = presets[preset](serviceName);

  return initGlobalLogger(config);
}

/**
 * 创建同步 Logger 代理
 * 用于导出，支持异步初始化
 *
 * 修复版本：确保链式调用的同步性
 */
export function createLoggerProxy(serviceName: string): IEnhancedLogger {
  const handler: ProxyHandler<any> = {
    get(target, prop) {
      // 如果 logger 已经初始化，直接使用
      if (globalLogger) {
        const value = globalLogger[prop as keyof IEnhancedLogger];

        // 如果是方法，需要绑定正确的 this 上下文
        if (typeof value === "function") {
          return value.bind(globalLogger);
        }
        return value;
      }

      // 如果还未初始化，需要区分不同类型的方法
      if (typeof prop === "string") {
        // 返回 logger 子对象的方法（需要返回代理对象）
        const chainableMethods = [
          "child",
          "forRequest",
          "forUser",
          "forModule",
        ];
        if (chainableMethods.includes(prop)) {
          return (...args: any[]) => {
            // 返回一个新的代理对象，它会在调用时等待初始化
            return createChainedLoggerProxy(serviceName, prop, args);
          };
        }

        // 普通日志方法（可以异步执行）
        const logMethods = [
          "debug",
          "info",
          "warn",
          "error",
          "logError",
          "logPerformance",
        ];
        if (logMethods.includes(prop)) {
          return async (...args: any[]) => {
            const logger = await getGlobalLogger(serviceName);
            const method = logger[prop as keyof IEnhancedLogger];
            if (typeof method === "function") {
              return (method as any).apply(logger, args);
            }
            return method;
          };
        }
      }

      // 其他属性的默认处理
      return async (...args: any[]) => {
        const logger = await getGlobalLogger(serviceName);
        const method = logger[prop as keyof IEnhancedLogger];
        if (typeof method === "function") {
          return (method as any).apply(logger, args);
        }
        return method;
      };
    },
  };

  return new Proxy({}, handler) as IEnhancedLogger;
}

/**
 * 创建链式调用的代理对象
 * 用于处理 child(), forRequest() 等返回 logger 子对象的方法
 */
function createChainedLoggerProxy(
  serviceName: string,
  methodName: string,
  methodArgs: any[]
): IEnhancedLogger {
  const handler: ProxyHandler<any> = {
    get(target, prop) {
      // 如果 globalLogger 已经初始化，直接同步返回
      if (globalLogger) {
        const chainMethod = globalLogger[methodName as keyof IEnhancedLogger];
        if (typeof chainMethod === "function") {
          const childLogger = (chainMethod as any).apply(globalLogger, methodArgs);
          const targetMethod = childLogger[prop as keyof IEnhancedLogger];
          if (typeof targetMethod === "function") {
            return targetMethod.bind(childLogger);
          }
          return targetMethod;
        }
      }

      // 如果还未初始化，返回异步执行的方法
      return async (...args: any[]) => {
        const logger = await getGlobalLogger(serviceName);

        // 先调用链式方法获取子 logger
        const chainMethod = logger[methodName as keyof IEnhancedLogger];
        if (typeof chainMethod === "function") {
          const childLogger = (chainMethod as any).apply(logger, methodArgs);

          // 然后调用子 logger 的方法
          const targetMethod = childLogger[prop as keyof IEnhancedLogger];
          if (typeof targetMethod === "function") {
            return (targetMethod as any).apply(childLogger, args);
          }
          return targetMethod;
        }

        throw new Error(`Method ${methodName} not found on logger`);
      };
    },
  };

  return new Proxy({}, handler) as IEnhancedLogger;
}

/**
 * 便捷函数：快速创建 Next.js 兼容的 Logger
 *
 * @param serviceName 服务名称
 * @returns Promise<IEnhancedLogger>
 */
export async function createNextjsLogger(
  serviceName: string
): Promise<IEnhancedLogger> {
  return createLoggerWithPreset(serviceName, "nextjsCompatible");
}

/**
 * 便捷函数：解决 Next.js 兼容性问题的快速方案
 *
 * @param serviceName 服务名称
 * @returns IEnhancedLogger (代理对象，支持异步初始化)
 */
export function createNextjsLoggerSync(serviceName: string): IEnhancedLogger {
  // 立即开始异步初始化
  createNextjsLogger(serviceName)
    .then((logger) => {
      globalLogger = logger;
    })
    .catch(console.error);

  return createLoggerProxy(serviceName);
}

// 导出工具函数
export { generateRequestId, generateTraceId };
