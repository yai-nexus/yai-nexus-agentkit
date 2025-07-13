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

import { config } from 'dotenv';
import { createLogger } from '@yai-nexus/pino-support';

// 加载环境变量
config();

async function main(): Promise<void> {
  console.log('启动 SLS 日志集成示例 (Pino 版本)...');
  try {
    // 1. 设置日志配置 (写入当前小时目录)  
    // 注意：pino-support 不支持 hourly strategy，只能写入固定路径
    const now = new Date();
    const currentHour = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(now.getHours()).padStart(2, '0')}`;
    const logPath = `../../logs/${currentHour}/sls-pino-example.log`;
    
    const logger = createLogger({
      serviceName: 'sls-pino-example',
      level: 'debug',
      console: { enabled: true, pretty: true },
      file: { enabled: true, path: logPath }
    });

    logger.info('服务启动', { service: 'sls-pino-example', version: '0.1.0' });
    logger.info('结构化日志演示', { foo: 'bar', time: new Date().toISOString() });
    logger.warn('警告日志演示', { userId: 'demo_user' });
    try {
      throw new Error('演示错误');
    } catch (error) {
      logger.error('捕获异常', {
        error: {
          name: (error as Error).name,
          message: (error as Error).message,
          stack: (error as Error).stack
        }
      });
    }
    logger.info('日志演示结束，日志文件位置: ../../logs/current/sls-pino-example.log');
  } catch (error) {
    console.error('SLS 集成失败:', error);
    process.exit(1);
  }
}

// 优雅停机处理
function setupGracefulShutdown() {
  const shutdown = () => {
    console.log('收到退出信号，正在优雅停机...');
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

setupGracefulShutdown();

// 运行主函数
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('程序执行失败:', error);
    process.exit(1);
  });
}