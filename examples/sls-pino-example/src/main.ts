#!/usr/bin/env node
/**
 * SLS 日志集成示例 - Pino 版本
 *
 * 演示如何使用 @yai-nexus/pino-support 将 pino 日志发送到阿里云 SLS。
 * 与 sls-loguru-example 功能等价，展示跨技术栈的统一日志体验。
 *
 * 运行前需要设置环境变量：
 * export SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
 * export SLS_AK_ID=your_access_key_id
 * export SLS_AK_KEY=your_access_key_secret
 * export SLS_PROJECT=your_project
 * export SLS_LOGSTORE=your_logstore
 */

import { createEnhancedLogger, presets } from "@yai-nexus/pino-support";
import { config } from "dotenv";

// 加载环境变量
config();

async function main(): Promise<void> {
  console.log("启动 SLS 日志集成示例 (Pino 版本)...");
  try {
    // 1. 使用脚本预设创建增强 logger
    // 自动支持按小时分目录，无需手动计算路径
    const logger = await createEnhancedLogger({
      serviceName: "sls-pino-example",
      ...presets.script("../../logs"),
    });

    logger.info("服务启动", { service: "sls-pino-example", version: "0.1.0" });

    // 演示增强 logger 的便捷方法
    const userLogger = logger.forUser("demo_user");
    const dbLogger = logger.forModule("database");

    logger.info("结构化日志演示", {
      foo: "bar",
      time: new Date().toISOString(),
    });

    // 演示性能日志
    dbLogger.logPerformance("query_users", 45, {
      query: "SELECT * FROM users",
      rows: 156,
    });

    // 演示用户相关日志
    userLogger.warn("用户操作警告", { action: "login_attempt" });

    // 演示错误日志的便捷方法
    try {
      throw new Error("演示错误");
    } catch (error) {
      if (error instanceof Error) {
        logger.logError(error, { context: "demo_operation" });
      }
    }
    logger.info(
      "日志演示结束，日志文件位置: ../../logs/current/sls-pino-example.log"
    );
  } catch (error) {
    console.error("SLS 集成失败:", error);
    process.exit(1);
  }
}

// 优雅停机处理
function setupGracefulShutdown() {
  const shutdown = () => {
    console.log("收到退出信号，正在优雅停机...");
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

setupGracefulShutdown();

// 运行主函数
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error("程序执行失败:", error);
    process.exit(1);
  });
}
