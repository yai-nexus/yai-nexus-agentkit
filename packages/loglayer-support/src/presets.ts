/**
 * 配置预设模块
 *
 * 提供常用的日志配置预设
 */

import type { EnvironmentConfig, LoggerConfig } from "./types";

/**
 * 默认环境配置
 */
export const defaultConfigs: LoggerConfig["environments"] = {
  development: {
    server: {
      preferredTransport: "pino",
      fallbackTransport: "winston",
      transportOptions: {
        pino: {
          level: "debug",
          pretty: true,
          streams: [{ stream: process.stdout }, { stream: "logs/app.log" }],
        },
        winston: {
          level: "debug",
          format: "pretty",
          transports: ["console", "file"],
        },
      },
      plugins: [
        {
          name: "redaction",
          config: { paths: ["password", "token"], censor: "[REDACTED]" },
        },
      ],
    },
    client: {
      preferredTransport: "console",
      fallbackTransport: "simplePrettyTerminal",
      transportOptions: {
        console: {
          level: "debug",
          pretty: true,
        },
        simplePrettyTerminal: {
          level: "debug",
          colorize: true,
        },
      },
    },
  },

  production: {
    server: {
      preferredTransport: "pino",
      fallbackTransport: "winston",
      transportOptions: {
        pino: {
          level: "info",
          pretty: false,
          streams: [
            { stream: process.stdout },
            { stream: "logs/app.log" },
            { stream: "logs/error.log", level: "error" },
          ],
        },
        winston: {
          level: "info",
          format: "json",
          transports: ["console", "file"],
        },
      },
      plugins: [
        {
          name: "redaction",
          config: {
            paths: ["password", "token", "apiKey"],
            censor: "[REDACTED]",
          },
        },
      ],
    },
    client: {
      preferredTransport: "console",
      fallbackTransport: "simplePrettyTerminal",
      transportOptions: {
        console: {
          level: "warn",
          pretty: false,
        },
        simplePrettyTerminal: {
          level: "warn",
          colorize: false,
        },
      },
    },
  },

  test: {
    server: {
      preferredTransport: "console",
      fallbackTransport: "simplePrettyTerminal",
      transportOptions: {
        console: {
          level: "error",
          pretty: false,
        },
      },
    },
    client: {
      preferredTransport: "console",
      fallbackTransport: "simplePrettyTerminal",
      transportOptions: {
        console: {
          level: "error",
          pretty: false,
        },
      },
    },
  },
};

/**
 * Next.js 兼容性配置
 * 当遇到 Next.js webpack 兼容性问题时使用
 */
export const nextjsCompatibilityConfig: EnvironmentConfig = {
  preferredTransport: "winston",
  fallbackTransport: "simplePrettyTerminal",
  transportOptions: {
    winston: {
      level: process.env.NODE_ENV === "production" ? "info" : "debug",
      format: "pretty",
      transports: ["console"],
    },
    simplePrettyTerminal: {
      level: process.env.NODE_ENV === "production" ? "info" : "debug",
      colorize: true,
    },
  },
  plugins: [
    {
      name: "redaction",
      config: { paths: ["password", "token"], censor: "[REDACTED]" },
    },
  ],
};

/**
 * 预设配置工厂函数
 */
export const presets = {
  /**
   * 开发环境预设
   */
  development: (serviceName: string): LoggerConfig => ({
    serviceName,
    environments: defaultConfigs,
  }),

  /**
   * 生产环境预设
   */
  production: (serviceName: string): LoggerConfig => ({
    serviceName,
    environments: defaultConfigs,
  }),

  /**
   * Next.js 兼容预设
   * 解决 Next.js webpack 兼容性问题
   */
  nextjsCompatible: (serviceName: string): LoggerConfig => ({
    serviceName,
    environments: defaultConfigs,
    forceConfig: {
      transport: "winston",
      reason: "Next.js pino compatibility issue",
    },
  }),

  /**
   * 测试环境预设
   */
  test: (serviceName: string): LoggerConfig => ({
    serviceName,
    environments: defaultConfigs,
    forceConfig: {
      transport: "console",
      reason: "Test environment - minimal logging",
    },
  }),

  /**
   * 控制台专用预设
   */
  consoleOnly: (serviceName: string): LoggerConfig => ({
    serviceName,
    environments: defaultConfigs,
    forceConfig: {
      transport: "console",
      reason: "Console only logging",
    },
  }),
};
