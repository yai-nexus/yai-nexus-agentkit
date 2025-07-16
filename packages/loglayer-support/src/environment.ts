/**
 * 环境检测模块
 *
 * 检测当前运行环境并提供环境相关的工具函数
 */

import type { EnvironmentInfo } from "./types";

/**
 * 检测当前运行环境
 */
export function detectEnvironment(): EnvironmentInfo {
  const isServer =
    typeof globalThis !== "undefined" &&
    typeof (globalThis as any).window === "undefined";
  const isClient = !isServer;

  // 检测 Next.js 环境
  const isNextJs =
    typeof process !== "undefined" &&
    (process.env.NEXT_RUNTIME !== undefined ||
      process.env.__NEXT_PRIVATE_PREBUNDLED_REACT !== undefined);

  // 环境类型检测
  const nodeEnv = process.env.NODE_ENV || "development";
  const isDevelopment = nodeEnv === "development";
  const isProduction = nodeEnv === "production";
  const isTest = nodeEnv === "test";

  // 平台检测
  let platform: "node" | "browser" | "nextjs" = "node";
  if (isClient) {
    platform = "browser";
  } else if (isNextJs) {
    platform = "nextjs";
  }

  return {
    isServer,
    isClient,
    isDevelopment,
    isProduction,
    isTest,
    environment: nodeEnv as "development" | "production" | "test",
    platform,
  };
}

/**
 * 检查是否支持文件操作
 */
export function supportsFileOperations(): boolean {
  try {
    return (
      typeof process !== "undefined" &&
      typeof process.versions !== "undefined" &&
      typeof process.versions.node !== "undefined"
    );
  } catch {
    return false;
  }
}

/**
 * 检查是否在 Next.js 环境中
 */
export function isNextJsEnvironment(): boolean {
  return (
    typeof process !== "undefined" &&
    (process.env.NEXT_RUNTIME !== undefined ||
      process.env.__NEXT_PRIVATE_PREBUNDLED_REACT !== undefined)
  );
}

/**
 * 检查是否在浏览器环境中
 */
export function isBrowserEnvironment(): boolean {
  return (
    typeof globalThis !== "undefined" &&
    typeof (globalThis as any).window !== "undefined" &&
    typeof (globalThis as any).window.document !== "undefined"
  );
}

/**
 * 检查是否在 Node.js 环境中
 */
export function isNodeEnvironment(): boolean {
  return (
    typeof process !== "undefined" &&
    process.versions != null &&
    process.versions.node != null
  );
}

/**
 * 获取环境变量，提供默认值
 */
export function getEnvVar(key: string, defaultValue: string = ""): string {
  if (typeof process === "undefined" || !process.env) {
    return defaultValue;
  }
  return process.env[key] || defaultValue;
}

/**
 * 检查是否在开发环境
 */
export function isDevelopment(): boolean {
  return getEnvVar("NODE_ENV", "development") === "development";
}

/**
 * 检查是否在生产环境
 */
export function isProduction(): boolean {
  return getEnvVar("NODE_ENV") === "production";
}

/**
 * 检查是否在测试环境
 */
export function isTest(): boolean {
  return getEnvVar("NODE_ENV") === "test";
}
