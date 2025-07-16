#!/usr/bin/env node
/**
 * @yai-nexus/loglayer-support 基础使用示例
 * 
 * 演示如何使用 loglayer-support 的各种功能
 */

import {
  createLoggerWithPreset,
  createNextjsLogger,
  createNextjsLoggerSync,
  detectEnvironment,
  generateRequestId,
  generateTraceId,
  presets
} from '@yai-nexus/loglayer-support';

console.log('🚀 @yai-nexus/loglayer-support 基础使用示例\n');

/**
 * 示例 1: 环境检测
 */
function exampleEnvironmentDetection() {
  console.log('📍 示例 1: 环境检测');
  console.log('=' .repeat(50));
  
  const env = detectEnvironment();
  console.log('当前环境信息:', {
    isServer: env.isServer,
    isClient: env.isClient,
    isDevelopment: env.isDevelopment,
    isProduction: env.isProduction,
    environment: env.environment,
    platform: env.platform
  });
  
  console.log('✅ 环境检测完成\n');
}

/**
 * 示例 2: 使用预设创建 Logger
 */
async function examplePresetLogger() {
  console.log('📍 示例 2: 使用预设创建 Logger');
  console.log('=' .repeat(50));
  
  // 使用开发环境预设
  const logger = await createLoggerWithPreset('demo-app', 'development');
  
  logger.info('使用预设创建的 Logger', { 
    preset: 'development',
    timestamp: new Date().toISOString()
  });
  
  // 测试不同日志级别
  logger.debug('Debug 级别日志');
  logger.info('Info 级别日志');
  logger.warn('Warning 级别日志');
  logger.error('Error 级别日志');
  
  console.log('✅ 预设 Logger 测试完成\n');
}

/**
 * 示例 3: 上下文绑定
 */
async function exampleContextBinding() {
  console.log('📍 示例 3: 上下文绑定');
  console.log('=' .repeat(50));
  
  const logger = await createLoggerWithPreset('context-demo', 'consoleOnly');
  
  // 生成 ID
  const requestId = generateRequestId();
  const traceId = generateTraceId();
  
  console.log('生成的 ID:', { requestId, traceId });
  
  // 请求级别的 logger
  const reqLogger = logger.forRequest(requestId, traceId);
  reqLogger.info('请求开始处理', { action: 'user_login' });
  
  // 用户级别的 logger
  const userLogger = logger.forUser('user123');
  userLogger.info('用户操作日志', { action: 'view_profile' });
  
  // 模块级别的 logger
  const dbLogger = logger.forModule('database');
  dbLogger.info('数据库操作', { 
    query: 'SELECT * FROM users',
    duration: '45ms'
  });
  
  // 子 logger
  const childLogger = logger.child({ 
    component: 'auth',
    version: '1.2.0'
  });
  childLogger.info('认证组件日志', { result: 'success' });
  
  console.log('✅ 上下文绑定测试完成\n');
}

/**
 * 示例 4: 增强方法
 */
async function exampleEnhancedMethods() {
  console.log('📍 示例 4: 增强方法');
  console.log('=' .repeat(50));
  
  const logger = await createLoggerWithPreset('enhanced-demo', 'consoleOnly');
  
  // 性能日志
  logger.logPerformance('api_call', 150, {
    endpoint: '/api/users',
    method: 'GET',
    statusCode: 200
  });
  
  logger.logPerformance('database_query', 45, {
    table: 'users',
    type: 'SELECT'
  });
  
  // 错误日志
  try {
    throw new Error('模拟业务错误');
  } catch (error) {
    logger.logError(error, {
      context: 'user_registration',
      userId: 'user123',
      step: 'email_validation'
    }, '用户注册失败');
  }
  
  console.log('✅ 增强方法测试完成\n');
}

/**
 * 示例 5: Next.js 兼容性
 */
async function exampleNextjsCompatibility() {
  console.log('📍 示例 5: Next.js 兼容性');
  console.log('=' .repeat(50));
  
  // 异步创建
  const asyncLogger = await createNextjsLogger('nextjs-async');
  asyncLogger.info('Next.js 异步 Logger 测试', {
    type: 'async',
    compatible: true
  });
  
  // 同步创建（推荐用于导出）
  const syncLogger = createNextjsLoggerSync('nextjs-sync');
  syncLogger.info('Next.js 同步 Logger 测试', {
    type: 'sync',
    compatible: true,
    note: '内部异步初始化，API 同步'
  });
  
  console.log('✅ Next.js 兼容性测试完成\n');
}

/**
 * 示例 6: 预设配置对比
 */
async function examplePresetComparison() {
  console.log('📍 示例 6: 预设配置对比');
  console.log('=' .repeat(50));
  
  const presetNames = ['development', 'production', 'nextjsCompatible', 'test', 'consoleOnly'];
  
  for (const presetName of presetNames) {
    console.log(`\n🔧 测试预设: ${presetName}`);
    try {
      const logger = await createLoggerWithPreset('preset-test', presetName);
      logger.info(`${presetName} 预设测试`, {
        preset: presetName,
        status: 'success'
      });
    } catch (error) {
      console.error(`❌ ${presetName} 预设失败:`, error.message);
    }
  }
  
  console.log('\n✅ 预设配置对比完成\n');
}

/**
 * 主函数
 */
async function main() {
  try {
    exampleEnvironmentDetection();
    await examplePresetLogger();
    await exampleContextBinding();
    await exampleEnhancedMethods();
    await exampleNextjsCompatibility();
    await examplePresetComparison();
    
    console.log('🎉 所有基础使用示例执行完成！');
    console.log('\n💡 更多示例:');
    console.log('  npm run test:transports  - 传输器测试');
    console.log('  npm run test:wrapper     - 包装器测试');
    console.log('  npm run test:compatibility - 兼容性测试');
    console.log('  npm run test:migration   - 迁移示例');
    
  } catch (error) {
    console.error('❌ 示例执行失败:', error);
    process.exit(1);
  }
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
