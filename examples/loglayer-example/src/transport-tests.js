#!/usr/bin/env node
/**
 * 传输器测试示例
 * 
 * 测试各种 LogLayer 传输器的功能和兼容性
 */

import { LogLayer } from 'loglayer';

console.log('🔧 LogLayer 传输器测试\n');

/**
 * 测试 Console 传输器
 */
async function testConsoleTransport() {
  console.log('📍 测试 Console 传输器');
  console.log('=' .repeat(50));
  
  try {
    const { ConsoleTransport } = await import('loglayer');
    
    const logger = new LogLayer({
      transport: new ConsoleTransport({
        logger: console
      })
    });
    
    logger.info('Console 传输器测试', { 
      transport: 'console',
      test: 'basic_functionality'
    });
    
    logger
      .withContext({ component: 'transport-test' })
      .withMetadata({ testId: 'console-001' })
      .info('Console 传输器上下文测试');
    
    console.log('✅ Console 传输器测试通过\n');
    return true;
  } catch (error) {
    console.error('❌ Console 传输器测试失败:', error.message);
    return false;
  }
}

/**
 * 测试 Winston 传输器
 */
async function testWinstonTransport() {
  console.log('📍 测试 Winston 传输器');
  console.log('=' .repeat(50));
  
  try {
    const { WinstonTransport } = await import('@loglayer/transport-winston');
    const winston = await import('winston');
    
    const winstonLogger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        })
      ]
    });
    
    const logger = new LogLayer({
      transport: new WinstonTransport({
        logger: winstonLogger
      })
    });
    
    logger.info('Winston 传输器测试', { 
      transport: 'winston',
      test: 'basic_functionality'
    });
    
    logger
      .withContext({ component: 'transport-test' })
      .withMetadata({ testId: 'winston-001' })
      .warn('Winston 传输器警告测试');
    
    console.log('✅ Winston 传输器测试通过\n');
    return true;
  } catch (error) {
    console.error('❌ Winston 传输器测试失败:', error.message);
    console.error('💡 请确保已安装: npm install @loglayer/transport-winston winston');
    return false;
  }
}

/**
 * 测试 Pino 传输器
 */
async function testPinoTransport() {
  console.log('📍 测试 Pino 传输器');
  console.log('=' .repeat(50));
  
  try {
    const { PinoTransport } = await import('@loglayer/transport-pino');
    const { pino } = await import('pino');
    
    const pinoLogger = pino({
      level: 'info',
      transport: {
        target: 'pino-pretty',
        options: {
          colorize: true
        }
      }
    });
    
    const logger = new LogLayer({
      transport: new PinoTransport({
        logger: pinoLogger
      })
    });
    
    logger.info('Pino 传输器测试', { 
      transport: 'pino',
      test: 'basic_functionality'
    });
    
    logger
      .withContext({ component: 'transport-test' })
      .withMetadata({ testId: 'pino-001' })
      .error('Pino 传输器错误测试');
    
    console.log('✅ Pino 传输器测试通过\n');
    return true;
  } catch (error) {
    console.error('❌ Pino 传输器测试失败:', error.message);
    console.error('💡 请确保已安装: npm install @loglayer/transport-pino pino pino-pretty');
    return false;
  }
}

/**
 * 测试 SimplePrettyTerminal 传输器
 */
async function testSimplePrettyTerminalTransport() {
  console.log('📍 测试 SimplePrettyTerminal 传输器');
  console.log('=' .repeat(50));
  
  try {
    const { SimplePrettyTerminalTransport } = await import('@loglayer/transport-simple-pretty-terminal');
    
    const logger = new LogLayer({
      transport: new SimplePrettyTerminalTransport({
        level: 'info',
        runtime: 'node'
      })
    });
    
    logger.info('SimplePrettyTerminal 传输器测试', { 
      transport: 'simplePrettyTerminal',
      test: 'basic_functionality'
    });
    
    logger
      .withContext({ component: 'transport-test' })
      .withMetadata({ testId: 'spt-001' })
      .debug('SimplePrettyTerminal 传输器调试测试');
    
    console.log('✅ SimplePrettyTerminal 传输器测试通过\n');
    return true;
  } catch (error) {
    console.error('❌ SimplePrettyTerminal 传输器测试失败:', error.message);
    console.error('💡 请确保已安装: npm install @loglayer/transport-simple-pretty-terminal');
    return false;
  }
}

/**
 * 测试 Redaction 插件
 */
async function testRedactionPlugin() {
  console.log('📍 测试 Redaction 插件');
  console.log('=' .repeat(50));
  
  try {
    const { redactionPlugin } = await import('@loglayer/plugin-redaction');
    const { ConsoleTransport } = await import('loglayer');
    
    const logger = new LogLayer({
      transport: new ConsoleTransport({
        logger: console
      }),
      plugins: [
        redactionPlugin({
          paths: ['password', 'token', 'apiKey', 'secret'],
          censor: '[REDACTED]'
        })
      ]
    });
    
    logger.info('Redaction 插件测试', { 
      username: 'testuser',
      password: 'secret123',  // 应该被脱敏
      token: 'abc123xyz',     // 应该被脱敏
      apiKey: 'key_12345',    // 应该被脱敏
      publicData: 'visible',  // 不应该被脱敏
      nested: {
        secret: 'hidden',     // 应该被脱敏
        normal: 'visible'     // 不应该被脱敏
      }
    });
    
    console.log('✅ Redaction 插件测试通过\n');
    return true;
  } catch (error) {
    console.error('❌ Redaction 插件测试失败:', error.message);
    console.error('💡 请确保已安装: npm install @loglayer/plugin-redaction');
    return false;
  }
}

/**
 * 传输器性能对比测试
 */
async function performanceComparison() {
  console.log('📍 传输器性能对比');
  console.log('=' .repeat(50));
  
  const testCount = 1000;
  const testMessage = 'Performance test message';
  const testMetadata = { 
    test: 'performance',
    iteration: 0,
    timestamp: new Date().toISOString()
  };
  
  // 测试 Console 传输器性能
  try {
    const { ConsoleTransport } = await import('loglayer');
    const logger = new LogLayer({
      transport: new ConsoleTransport({ logger: console })
    });
    
    const start = Date.now();
    for (let i = 0; i < testCount; i++) {
      logger.info(testMessage, { ...testMetadata, iteration: i });
    }
    const duration = Date.now() - start;
    
    console.log(`Console 传输器: ${testCount} 条日志耗时 ${duration}ms (${(testCount/duration*1000).toFixed(0)} logs/sec)`);
  } catch (error) {
    console.error('Console 传输器性能测试失败:', error.message);
  }
  
  console.log('✅ 性能对比测试完成\n');
}

/**
 * 主函数
 */
async function main() {
  const results = [];
  
  console.log('🚀 开始传输器测试\n');
  
  // 执行所有测试
  results.push(await testConsoleTransport());
  results.push(await testWinstonTransport());
  results.push(await testPinoTransport());
  results.push(await testSimplePrettyTerminalTransport());
  results.push(await testRedactionPlugin());
  
  // 性能测试
  await performanceComparison();
  
  // 统计结果
  const passed = results.filter(r => r).length;
  const total = results.length;
  
  console.log('📊 测试结果统计');
  console.log('=' .repeat(50));
  console.log(`总测试数: ${total}`);
  console.log(`通过测试: ${passed}`);
  console.log(`失败测试: ${total - passed}`);
  
  if (passed === total) {
    console.log('\n🎉 所有传输器测试通过！');
    process.exit(0);
  } else {
    console.log('\n❌ 部分传输器测试失败');
    console.log('💡 请检查相关依赖是否正确安装');
    process.exit(1);
  }
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
