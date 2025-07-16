#!/usr/bin/env node
/**
 * 测试构建后的包
 * 
 * 验证构建后的 @yai-nexus/loglayer-support 包是否正常工作
 */

async function testBuiltPackage() {
  console.log('🚀 测试构建后的包...\n');
  
  try {
    // 导入构建后的包
    const {
      createLoggerWithPreset,
      createNextjsLogger,
      createNextjsLoggerSync,
      detectEnvironment,
      generateRequestId,
      generateTraceId,
      presets
    } = require('./dist/index.js');
    
    console.log('✅ 包导入成功');
    
    // 测试环境检测
    console.log('\n🔧 测试环境检测...');
    const env = detectEnvironment();
    console.log('环境信息:', {
      isServer: env.isServer,
      isClient: env.isClient,
      environment: env.environment,
      platform: env.platform
    });
    console.log('✅ 环境检测正常');
    
    // 测试工具函数
    console.log('\n🔧 测试工具函数...');
    const requestId = generateRequestId();
    const traceId = generateTraceId();
    console.log('生成的 ID:', { requestId, traceId });
    console.log('✅ 工具函数正常');
    
    // 测试预设
    console.log('\n🔧 测试预设配置...');
    const config = presets.development('test-service');
    console.log('预设配置:', config.serviceName);
    console.log('✅ 预设配置正常');
    
    // 测试 Logger 创建（使用 console 传输器避免依赖问题）
    console.log('\n🔧 测试 Logger 创建...');
    const logger = await createLoggerWithPreset('test-service', 'consoleOnly');
    
    // 测试基础日志
    logger.info('测试消息', { test: true });
    
    // 测试上下文绑定
    const reqLogger = logger.forRequest(requestId, traceId);
    reqLogger.info('请求日志测试');
    
    // 测试模块日志
    const moduleLogger = logger.forModule('test-module');
    moduleLogger.info('模块日志测试');
    
    // 测试性能日志
    logger.logPerformance('test_operation', 100, { success: true });
    
    // 测试错误日志
    const testError = new Error('测试错误');
    logger.logError(testError, { context: 'test' });
    
    console.log('✅ Logger 功能测试通过');
    
    // 测试 Next.js 同步 Logger
    console.log('\n🔧 测试 Next.js 同步 Logger...');
    const nextjsLogger = createNextjsLoggerSync('nextjs-test');
    nextjsLogger.info('Next.js 同步 Logger 测试');
    console.log('✅ Next.js 同步 Logger 正常');
    
    console.log('\n🎉 所有测试通过！包构建成功且功能正常。');
    return true;
    
  } catch (error) {
    console.error('❌ 测试失败:', error);
    console.error('错误堆栈:', error.stack);
    return false;
  }
}

// 运行测试
testBuiltPackage().then(success => {
  process.exit(success ? 0 : 1);
});
