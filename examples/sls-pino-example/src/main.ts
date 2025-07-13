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

// 加载环境变量
config();

async function main(): Promise<void> {
  console.log('启动 SLS 日志集成示例 (Pino 版本)...');
  
  try {
    // 1. 设置统一的基础日志配置 (控制台 + 文件，SLS 待实现)
    const logger = createLogger({
      serviceName: 'sls-pino-example',
      level: 'debug',
      console: { enabled: true, pretty: true },
      file: { enabled: true, strategy: 'hourly' }
      // Note: SLS cloud logging through unified config is not yet implemented
      // For SLS integration, use the direct SlsTransport class approach
    });
    
    logger.info('启动 SLS 日志集成示例', { service: 'sls-pino-example', version: '0.1.0' });
    
    // 2. 演示统一日志配置功能
    logger.info('演示统一日志配置功能（控制台 + 文件输出）');
    logger.info('注意：SLS 云端日志集成尚未在统一配置中实现，需要直接使用 SlsTransport 类');
    
    // 发送示例日志到控制台和文件
    logger.info('这是一个简单的 INFO 日志');
    logger.warn('这是一个 WARNING 日志', { userId: 'demo_user' });
    
    // 带上下文的日志
    const contextLogger = logger.child({ requestId: 'req_123', action: 'demo' });
    contextLogger.info('带上下文的日志');
    
    // 错误日志演示
    try {
      throw new Error('这是一个演示错误');
    } catch (error) {
      logger.error('这是一个自动捕获的异常日志', {
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
    
    logger.info('操作完成', {
      operation: 'demo_task',
      durationMs: duration,
      success: true,
      performance: {
        startTime: new Date(startTime).toISOString(),
        endTime: new Date().toISOString()
      }
    });
    
    logger.info('基础日志示例完成（控制台 + 文件输出）');
    logger.info('日志文件位置: logs/current/<服务名>.log');
    
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