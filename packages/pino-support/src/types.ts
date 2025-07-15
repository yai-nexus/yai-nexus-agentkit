/**
 * Types for pino-support with directory strategy support
 */

import { DirectoryStrategy } from "./strategies";

export interface LoggerConfig {
  serviceName: string;
  level?: "trace" | "debug" | "info" | "warn" | "error" | "fatal";
  console?: {
    enabled?: boolean;
    pretty?: boolean;
  };
  file?: {
    enabled?: boolean;
    path?: string; // 简单文件路径（与 strategy 互斥）
    pretty?: boolean; // 启用文件输出的美化格式
    strategy?: "hourly" | "daily" | "simple" | DirectoryStrategy; // 目录策略
    baseDir?: string; // 基础目录，默认 "logs"
    maxSize?: string; // 文件大小限制（暂未实现）
    maxFiles?: number; // 文件数量限制（暂未实现）
  };
  cloud?: {
    enabled?: boolean;
    sls?: {
      endpoint?: string;
      accessKeyId?: string;
      accessKeySecret?: string;
      project?: string;
      logstore?: string;
    };
  };
}

/**
 * Environment detection result
 */
export interface EnvironmentInfo {
  /** Is running in browser environment */
  isBrowser: boolean;
  /** Is running in Node.js environment */
  isNode: boolean;
  /** Environment type for logging purposes */
  environment: "browser" | "node" | "unknown";
}
