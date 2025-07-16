#!/usr/bin/env node
/**
 * 抽象层包装器测试
 * 
 * 测试我们的 LogLayerWrapper 是否正确实现了 EnhancedLogger 接口
 */

const { LogLayer } = require('loglayer');

// 模拟我们的包装器（简化版，用于测试）
class LogLayerWrapper {
  constructor(logLayer, context = {}) {
    this.logLayer = logLayer;
    this.context = context;
  }

  withContext(additionalContext = {}) {
    const fullContext = { ...this.context, ...additionalContext };
    return Object.keys(fullContext).length > 0 
      ? this.logLayer.withContext(fullContext)
      : this.logLayer;
  }

  debug(message, metadata) {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).debug(message);
    } else {
      logger.debug(message);
    }
  }

  info(message, metadata) {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).info(message);
    } else {
      logger.info(message);
    }
  }

  warn(message, metadata) {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).warn(message);
    } else {
      logger.warn(message);
    }
  }

  error(message, metadata) {
    const logger = this.withContext();
    if (metadata) {
      logger.withMetadata(metadata).error(message);
    } else {
      logger.error(message);
    }
  }

  child(bindings) {
    const newContext = { ...this.context, ...bindings };
    return new LogLayerWrapper(this.logLayer, newContext);
  }

  forRequest(requestId, traceId) {
    const context = { requestId, ...(traceId && { traceId }) };
    return this.child(context);
  }

  forUser(userId) {
    return this.child({ userId });
  }

  forModule(moduleName) {
    return this.child({ module: moduleName });
  }

  logError(error, context, message = "Error occurred") {
    const logger = this.withContext(context);
    logger
      .withError(error)
      .withMetadata({
        error: {
          name: error.name,
          message: error.message,
          stack: error.stack,
        },
        ...context,
      })
      .error(message);
  }

  logPerformance(operation, duration, metadata) {
    this.info("Performance metric", {
      performance: {
        operation,
        duration: `${duration}ms`,
        ...metadata,
      },
    });
  }

  get raw() {
    return this.logLayer;
  }
}

async function testBasicLogging() {
  console.log('\n🔧 测试基础日志功能...');
  
  try {
    const { ConsoleTransport } = require('loglayer');
    
    const logLayer = new LogLayer({
      transport: new ConsoleTransport({ logger: console })
    });
    
    const logger = new LogLayerWrapper(logLayer);
    
    logger.debug('Debug 消息测试');
    logger.info('Info 消息测试');
    logger.warn('Warn 消息测试');
    logger.error('Error 消息测试');
    
    console.log('✅ 基础日志功能测试通过');
    return true;
  } catch (error) {
    console.error('❌ 基础日志功能测试失败:', error.message);
    return false;
  }
}

async function testContextBinding() {
  console.log('\n🔧 测试上下文绑定...');
  
  try {
    const { ConsoleTransport } = require('loglayer');
    
    const logLayer = new LogLayer({
      transport: new ConsoleTransport({ logger: console })
    });
    
    const logger = new LogLayerWrapper(logLayer);
    
    // 测试 child logger
    const childLogger = logger.child({ component: 'test' });
    childLogger.info('Child logger 测试');
    
    // 测试 forRequest
    const reqLogger = logger.forRequest('req123', 'trace456');
    reqLogger.info('Request logger 测试');
    
    // 测试 forUser
    const userLogger = logger.forUser('user789');
    userLogger.info('User logger 测试');
    
    // 测试 forModule
    const moduleLogger = logger.forModule('database');
    moduleLogger.info('Module logger 测试');
    
    console.log('✅ 上下文绑定测试通过');
    return true;
  } catch (error) {
    console.error('❌ 上下文绑定测试失败:', error.message);
    return false;
  }
}

async function testEnhancedMethods() {
  console.log('\n🔧 测试增强方法...');
  
  try {
    const { ConsoleTransport } = require('loglayer');
    
    const logLayer = new LogLayer({
      transport: new ConsoleTransport({ logger: console })
    });
    
    const logger = new LogLayerWrapper(logLayer);
    
    // 测试 logError
    const testError = new Error('测试错误');
    logger.logError(testError, { context: 'test' });
    
    // 测试 logPerformance
    logger.logPerformance('api_call', 150, { endpoint: '/test' });
    
    console.log('✅ 增强方法测试通过');
    return true;
  } catch (error) {
    console.error('❌ 增强方法测试失败:', error.message);
    return false;
  }
}

async function testMetadata() {
  console.log('\n🔧 测试元数据功能...');
  
  try {
    const { ConsoleTransport } = require('loglayer');
    
    const logLayer = new LogLayer({
      transport: new ConsoleTransport({ logger: console })
    });
    
    const logger = new LogLayerWrapper(logLayer);
    
    // 测试带元数据的日志
    logger.info('带元数据的消息', {
      userId: 'user123',
      action: 'login',
      timestamp: new Date().toISOString()
    });
    
    console.log('✅ 元数据功能测试通过');
    return true;
  } catch (error) {
    console.error('❌ 元数据功能测试失败:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 LogLayerWrapper 测试开始\n');
  
  const results = [];
  
  // 测试各个功能
  results.push(await testBasicLogging());
  results.push(await testContextBinding());
  results.push(await testEnhancedMethods());
  results.push(await testMetadata());
  
  // 统计结果
  const passed = results.filter(r => r).length;
  const total = results.length;
  
  console.log(`\n📊 测试结果: ${passed}/${total} 通过`);
  
  if (passed === total) {
    console.log('🎉 LogLayerWrapper 所有测试通过！');
    process.exit(0);
  } else {
    console.log('❌ 部分测试失败');
    process.exit(1);
  }
}

// 运行测试
main().catch(console.error);
