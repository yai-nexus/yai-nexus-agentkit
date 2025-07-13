#!/usr/bin/env node
/**
 * SLS 日志集成示例 - Pino 版本
 *
 * 演示如何使用 @yai-nexus/pino-support 将 pino 日志发送到阿里云 SLS。
 * 与 sls-loguru-example 功能等价，展示跨技术栈的统一日志体验。
 *
 * 这个示例展示了：
 * 1. 使用统一的日志配置（控制台 + 文件）
 * 2. 添加 SLS transport 进行云端日志收集
 * 3. 发送结构化日志消息
 * 4. 优雅停机确保日志完整发送
 *
 * 运行前需要设置环境变量：
 * export SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
 * export SLS_AK_ID=your_access_key_id
 * export SLS_AK_KEY=your_access_key_secret
 * export SLS_PROJECT=your_project
 * export SLS_LOGSTORE=your_logstore
 */

import { config } from 'dotenv';
import { createLogger, getLoggerMetadata } from '@yai-nexus/pino-support';
import { SlsTransport } from '@yai-nexus/pino-support/sls';

// 加载环境变量
config();

async function main(): Promise<void> {
  console.log('启动 SLS 日志集成示例 (Pino 版本)...');
  
  try {
    // 1. 设置统一的基础日志配置 (控制台 + 文件)
    const logger = createLogger({
      serviceName: 'sls-pino-example',
      level: 'info',
      console: { enabled: true, pretty: true },
      file: { enabled: true, strategy: 'hourly' }
    });
    
    logger.info('启动 SLS 日志集成示例', { service: 'sls-pino-example', version: '0.1.0' });
    
    // 2. 检查必要的环境变量
    const requiredVars = ['SLS_ENDPOINT', 'SLS_AK_ID', 'SLS_AK_KEY', 'SLS_PROJECT', 'SLS_LOGSTORE'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      logger.error('缺少必要的环境变量', { missingVars });
      logger.error('请参考 README.md 设置环境变量');
      return;
    }
    
    // 3. 创建 SLS Transport
    const slsTransport = new SlsTransport({
      endpoint: process.env.SLS_ENDPOINT!,
      accessKeyId: process.env.SLS_AK_ID!,
      accessKeySecret: process.env.SLS_AK_KEY!,
      project: process.env.SLS_PROJECT!,
      logstore: process.env.SLS_LOGSTORE!,
      level: 'info'
    });
    
    // 4. 启动 SLS Transport
    await slsTransport.start();
    
    // 5. 创建带 SLS transport 的新 logger
    const loggerWithSls = createLogger({
      serviceName: 'sls-pino-example',
      level: 'info',
      console: { enabled: true, pretty: true },
      file: { enabled: true, strategy: 'hourly' },
      cloud: {
        enabled: true,
        sls: {
          endpoint: process.env.SLS_ENDPOINT!,
          accessKeyId: process.env.SLS_AK_ID!,
          accessKeySecret: process.env.SLS_AK_KEY!,
          project: process.env.SLS_PROJECT!,
          logstore: process.env.SLS_LOGSTORE!
        }
      }
    });
    
    logger.info('SLS 日志集成已启用', {
      project: process.env.SLS_PROJECT,
      logstore: process.env.SLS_LOGSTORE,
      metadata: getLoggerMetadata(loggerWithSls)
    });
    
    // 6. 发送示例日志
    loggerWithSls.info('这是一个简单的 INFO 日志');
    loggerWithSls.warn('这是一个 WARNING 日志', { userId: 'demo_user' });
    
    // 带上下文的日志
    const contextLogger = loggerWithSls.child({ requestId: 'req_123', action: 'demo' });
    contextLogger.info('带上下文的日志');
    
    // 错误日志演示
    try {
      throw new Error('这是一个演示错误');
    } catch (error) {
      loggerWithSls.error('这是一个自动捕获的异常日志', {
        error: {
          name: (error as Error).name,
          message: (error as Error).message,
          stack: (error as Error).stack
        }
      });
    }
    
    // 结构化日志演示
    const startTime = Date.now();
    await new Promise(resolve => setTimeout(resolve, 100)); // 模拟一些工作
    const duration = Date.now() - startTime;
    
    loggerWithSls.info('操作完成', {
      operation: 'demo_task',
      durationMs: duration,
      success: true,
      performance: {
        startTime: new Date(startTime).toISOString(),
        endTime: new Date().toISOString()
      }
    });
    
    logger.info('示例运行结束，等待日志发送...');
    
    // 7. 等待批处理发送 (SLS 使用批量发送优化性能)
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // 8. 优雅停机
    await slsTransport.stop();
    
    logger.info('SLS 日志示例完成');
    
  } catch (error) {
    console.error('SLS 集成失败:', error);
    console.error('请检查环境变量配置和网络连接。');
    process.exit(1);
  }
}

// 设置优雅停机处理
process.on('SIGINT', async () => {
  console.log('\n收到 SIGINT 信号，正在优雅停机...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n收到 SIGTERM 信号，正在优雅停机...');
  process.exit(0);
});

// 运行主函数
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('程序执行失败:', error);
    process.exit(1);
  });
}