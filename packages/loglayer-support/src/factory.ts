/**
 * Logger 工厂模块
 *
 * 负责创建和配置 Logger 实例
 */

import { LogLayer } from "loglayer";
import { getEnvironmentConfig } from "./config";
import { TransportFactory } from "./transports";
import type {
  EnvironmentConfig,
  EnvironmentInfo,
  IEnhancedLogger,
  LoggerConfig,
} from "./types";
import { LogLayerWrapper } from "./wrapper";

/**
 * LogLayer 工厂类
 * 根据环境配置创建优化的 LogLayer 实例
 */
export class LogLayerFactory {
  /**
   * 创建 LogLayer 实例
   */
  static async createLogLayer(
    config: EnvironmentConfig,
    serviceName: string,
    env: EnvironmentInfo
  ): Promise<LogLayer> {
    let transport;
    let transportType = config.preferredTransport;

    try {
      // 尝试创建首选传输器
      transport = await TransportFactory.createTransport(
        transportType,
        config,
        serviceName
      );
    } catch (error) {
      console.warn(
        `Failed to create ${transportType} transport, falling back to ${config.fallbackTransport}:`,
        error
      );

      // 使用备选传输器
      transportType = config.fallbackTransport;
      transport = await TransportFactory.createTransport(
        transportType,
        config,
        serviceName
      );
    }

    // 创建插件
    const plugins = await TransportFactory.createPlugins(config.plugins);

    // 创建 LogLayer 实例
    const logLayer = new LogLayer({
      transport,
      plugins,
      // 配置字段名
      contextFieldName: "context",
      metadataFieldName: "metadata",
    });

    // 添加服务信息到上下文
    logLayer.withContext({
      service: serviceName,
      environment: env.environment,
      platform: env.platform,
      transportType,
    });

    return logLayer;
  }

  /**
   * 创建增强 Logger 包装器
   */
  static async createEnhancedLogger(
    config: LoggerConfig,
    env: EnvironmentInfo
  ): Promise<IEnhancedLogger> {
    // 获取环境配置
    const envConfig = getEnvironmentConfig(env, config);

    // 创建 LogLayer 实例
    const logLayer = await LogLayerFactory.createLogLayer(
      envConfig,
      config.serviceName,
      env
    );

    // 创建包装器
    const wrapper = new LogLayerWrapper(logLayer);

    // 记录初始化信息
    wrapper.info("Logger initialized", {
      serviceName: config.serviceName,
      environment: env.environment,
      platform: env.platform,
      transportType: envConfig.preferredTransport,
      version: "1.0.0",
    });

    return wrapper;
  }

  /**
   * 创建带有自动回退的 Logger
   */
  static async createResilientLogger(
    config: LoggerConfig,
    env: EnvironmentInfo
  ): Promise<IEnhancedLogger> {
    try {
      return await LogLayerFactory.createEnhancedLogger(config, env);
    } catch (error) {
      console.warn(
        "Failed to create logger with preferred config, using fallback:",
        error
      );

      // 使用最简单的配置作为最后的回退
      const fallbackConfig: LoggerConfig = {
        serviceName: config.serviceName,
        environments: config.environments,
        forceConfig: {
          transport: "console",
          reason: "Fallback due to initialization failure",
        },
      };

      return await LogLayerFactory.createEnhancedLogger(fallbackConfig, env);
    }
  }

  /**
   * 验证传输器可用性并创建 Logger
   */
  static async createValidatedLogger(
    config: LoggerConfig,
    env: EnvironmentInfo
  ): Promise<IEnhancedLogger> {
    const envConfig = getEnvironmentConfig(env, config);

    // 检查首选传输器是否可用
    const isPreferredAvailable = await TransportFactory.isTransportAvailable(
      envConfig.preferredTransport
    );

    if (!isPreferredAvailable) {
      console.warn(
        `Preferred transport ${envConfig.preferredTransport} is not available, using fallback`
      );

      // 修改配置使用备选传输器
      const modifiedConfig: LoggerConfig = {
        ...config,
        forceConfig: {
          transport: envConfig.fallbackTransport,
          reason: `Preferred transport ${envConfig.preferredTransport} not available`,
        },
      };

      return await LogLayerFactory.createEnhancedLogger(modifiedConfig, env);
    }

    return await LogLayerFactory.createEnhancedLogger(config, env);
  }
}
