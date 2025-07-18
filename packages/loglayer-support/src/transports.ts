/**
 * 传输器工厂模块
 *
 * 负责创建和管理各种 LogLayer 传输器
 */

import type { EnvironmentConfig } from "./types";

/**
 * 传输器工厂类
 * 根据配置创建相应的 LogLayer 传输器
 */
export class TransportFactory {
  /**
   * 创建传输器实例
   */
  static async createTransport(
    transportType: string,
    config: EnvironmentConfig,
    serviceName: string
  ): Promise<any> {
    const transportOptions =
      config.transportOptions[
        transportType as keyof typeof config.transportOptions
      ];

    switch (transportType) {
      case "pino":
        return await TransportFactory.createPinoTransport(
          transportOptions,
          serviceName
        );

      case "winston":
        return await TransportFactory.createWinstonTransport(
          transportOptions,
          serviceName
        );

      case "console":
        return await TransportFactory.createConsoleTransport(
          transportOptions,
          serviceName
        );

      case "simplePrettyTerminal":
        return await TransportFactory.createSimplePrettyTerminalTransport(
          transportOptions,
          serviceName
        );

      default:
        throw new Error(`Unsupported transport type: ${transportType}`);
    }
  }

  /**
   * 创建 Pino 传输器
   */
  private static async createPinoTransport(
    transportOptions: any,
    serviceName: string
  ): Promise<any> {
    const { PinoTransport } = await import("@loglayer/transport-pino");
    const { pino } = await import("pino");

    const pinoLogger = pino({
      level: transportOptions?.level || "info",
      base: {
        service: serviceName,
      },
      ...(transportOptions?.pretty && {
        transport: { target: "pino-pretty" },
      }),
    });

    return new PinoTransport({ logger: pinoLogger });
  }

  /**
   * 创建 Winston 传输器
   */
  private static async createWinstonTransport(
    transportOptions: any,
    serviceName: string
  ): Promise<any> {
    const { WinstonTransport } = await import("@loglayer/transport-winston");
    const winston = await import("winston");
    const path = await import("path");
    const fs = await import("fs");

    // 确保日志目录存在
    const logDir = path.resolve(process.cwd(), "logs/current");
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    const transports: any[] = [
      new winston.transports.Console({
        format:
          transportOptions?.format === "pretty"
            ? winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
              )
            : winston.format.json(),
      }),
    ];

    // 添加文件传输器
    transports.push(
      new winston.transports.File({
        filename: path.join(logDir, `${serviceName}.log`),
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.errors({ stack: true }),
          winston.format.json()
        ),
        maxsize: 10 * 1024 * 1024, // 10MB
        maxFiles: 5,
        tailable: true,
      })
    );

    const winstonLogger = winston.createLogger({
      level: transportOptions?.level || "info",
      defaultMeta: {
        service: serviceName,
      },
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports,
    });

    return new WinstonTransport({ logger: winstonLogger });
  }

  /**
   * 创建 Console 传输器
   */
  private static async createConsoleTransport(
    transportOptions: any,
    serviceName: string
  ): Promise<any> {
    const { ConsoleTransport } = await import("loglayer");
    return new ConsoleTransport({
      logger: console,
      level: transportOptions?.level || "info",
    });
  }

  /**
   * 创建简单终端传输器
   */
  private static async createSimplePrettyTerminalTransport(
    transportOptions: any,
    serviceName: string
  ): Promise<any> {
    const { SimplePrettyTerminalTransport } = await import(
      "@loglayer/transport-simple-pretty-terminal"
    );
    return new SimplePrettyTerminalTransport({
      level: transportOptions?.level || "info",
      runtime: "node",
    });
  }

  /**
   * 创建插件实例
   */
  static async createPlugins(
    pluginConfigs: EnvironmentConfig["plugins"] = []
  ): Promise<any[]> {
    const plugins = [];

    for (const pluginConfig of pluginConfigs) {
      try {
        const plugin = await TransportFactory.createPlugin(
          pluginConfig.name,
          pluginConfig.config || {}
        );
        if (plugin) {
          plugins.push(plugin);
        }
      } catch (error) {
        console.warn(`Failed to create plugin ${pluginConfig.name}:`, error);
      }
    }

    return plugins;
  }

  /**
   * 创建单个插件
   */
  private static async createPlugin(
    pluginName: string,
    config: Record<string, unknown>
  ): Promise<any> {
    switch (pluginName) {
      case "redaction": {
        const { redactionPlugin } = await import("@loglayer/plugin-redaction");
        return redactionPlugin(config);
      }
      // 可以添加更多插件
      default:
        console.warn(`Unknown plugin: ${pluginName}`);
        return null;
    }
  }

  /**
   * 检查传输器是否可用
   */
  static async isTransportAvailable(transportType: string): Promise<boolean> {
    try {
      switch (transportType) {
        case "pino":
          await import("@loglayer/transport-pino");
          await import("pino");
          return true;
        case "winston":
          await import("@loglayer/transport-winston");
          await import("winston");
          return true;
        case "console":
          return true; // Console 传输器总是可用的
        case "simplePrettyTerminal":
          await import("@loglayer/transport-simple-pretty-terminal");
          return true;
        default:
          return false;
      }
    } catch {
      return false;
    }
  }
}
