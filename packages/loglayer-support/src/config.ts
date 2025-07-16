/**
 * 配置管理模块
 * 
 * 处理日志配置的获取和管理
 */

import type { EnvironmentInfo, EnvironmentConfig, LoggerConfig } from './types';
import { defaultConfigs } from './presets';

/**
 * 根据环境信息获取配置
 */
export function getEnvironmentConfig(
  env: EnvironmentInfo,
  config: LoggerConfig
): EnvironmentConfig {
  // 如果有强制配置，优先使用
  if (config.forceConfig) {
    const baseConfig = config.environments[env.environment][env.isServer ? 'server' : 'client'];
    return {
      preferredTransport: config.forceConfig.transport,
      fallbackTransport: 'console',
      transportOptions: {
        [config.forceConfig.transport]: baseConfig.transportOptions[config.forceConfig.transport]
      },
      plugins: baseConfig.plugins
    };
  }
  
  // 根据环境选择配置
  const envConfig = config.environments[env.environment];
  return env.isServer ? envConfig.server : envConfig.client;
}

/**
 * 验证配置的有效性
 */
export function validateConfig(config: LoggerConfig): boolean {
  if (!config.serviceName) {
    console.error('Logger config validation failed: serviceName is required');
    return false;
  }

  if (!config.environments) {
    console.error('Logger config validation failed: environments is required');
    return false;
  }

  const requiredEnvs = ['development', 'production', 'test'] as const;
  for (const env of requiredEnvs) {
    if (!config.environments[env]) {
      console.error(`Logger config validation failed: environments.${env} is required`);
      return false;
    }

    if (!config.environments[env].server || !config.environments[env].client) {
      console.error(`Logger config validation failed: environments.${env} must have server and client configs`);
      return false;
    }
  }

  return true;
}

/**
 * 合并配置
 */
export function mergeConfigs(
  baseConfig: LoggerConfig,
  overrideConfig: Partial<LoggerConfig>
): LoggerConfig {
  return {
    ...baseConfig,
    ...overrideConfig,
    environments: {
      ...baseConfig.environments,
      ...overrideConfig.environments,
    },
  };
}

/**
 * 创建默认配置
 */
export function createDefaultConfig(serviceName: string): LoggerConfig {
  return {
    serviceName,
    environments: defaultConfigs,
  };
}

/**
 * 获取传输器优先级
 * 根据环境和平台返回推荐的传输器优先级列表
 */
export function getTransportPriority(env: EnvironmentInfo): string[] {
  if (env.isClient) {
    return ['console', 'simplePrettyTerminal'];
  }

  if (env.platform === 'nextjs') {
    // Next.js 环境优先使用兼容性好的传输器
    return ['winston', 'console', 'simplePrettyTerminal'];
  }

  if (env.isDevelopment) {
    return ['pino', 'winston', 'console'];
  }

  if (env.isProduction) {
    return ['pino', 'winston', 'console'];
  }

  // 测试环境
  return ['console', 'winston'];
}

/**
 * 检查传输器是否可用
 */
export async function isTransportAvailable(transportType: string): Promise<boolean> {
  try {
    switch (transportType) {
      case 'pino':
        await import('@loglayer/transport-pino');
        await import('pino');
        return true;
      case 'winston':
        await import('@loglayer/transport-winston');
        await import('winston');
        return true;
      case 'console':
        // Console 传输器总是可用的
        return true;
      case 'simplePrettyTerminal':
        await import('@loglayer/transport-simple-pretty-terminal');
        return true;
      default:
        return false;
    }
  } catch {
    return false;
  }
}

/**
 * 获取可用的传输器
 */
export async function getAvailableTransports(env: EnvironmentInfo): Promise<string[]> {
  const priority = getTransportPriority(env);
  const available: string[] = [];

  for (const transport of priority) {
    if (await isTransportAvailable(transport)) {
      available.push(transport);
    }
  }

  // 确保至少有 console 传输器可用
  if (available.length === 0) {
    available.push('console');
  }

  return available;
}
