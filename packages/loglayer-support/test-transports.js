#!/usr/bin/env node
/**
 * 传输器测试脚本
 * 
 * 验证各种 LogLayer 传输器是否正常工作
 */

const { LogLayer } = require('loglayer');

async function testConsoleTransport() {
  console.log('\n🔧 测试 Console 传输器...');
  
  try {
    const { ConsoleTransport } = require('loglayer');
    
    const logger = new LogLayer({
      transport: new ConsoleTransport({
        logger: console
      })
    });
    
    logger.info('Console 传输器测试成功', { test: 'console' });
    console.log('✅ Console 传输器工作正常');
    return true;
  } catch (error) {
    console.error('❌ Console 传输器测试失败:', error.message);
    return false;
  }
}

async function testWinstonTransport() {
  console.log('\n🔧 测试 Winston 传输器...');
  
  try {
    const { WinstonTransport } = require('@loglayer/transport-winston');
    const winston = require('winston');
    
    const winstonLogger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console()
      ]
    });
    
    const logger = new LogLayer({
      transport: new WinstonTransport({
        logger: winstonLogger
      })
    });
    
    logger.info('Winston 传输器测试成功', { test: 'winston' });
    console.log('✅ Winston 传输器工作正常');
    return true;
  } catch (error) {
    console.error('❌ Winston 传输器测试失败:', error.message);
    return false;
  }
}

async function testPinoTransport() {
  console.log('\n🔧 测试 Pino 传输器...');
  
  try {
    const { PinoTransport } = require('@loglayer/transport-pino');
    const pino = require('pino');
    
    const pinoLogger = pino({
      level: 'info'
    });
    
    const logger = new LogLayer({
      transport: new PinoTransport({
        logger: pinoLogger
      })
    });
    
    logger.info('Pino 传输器测试成功', { test: 'pino' });
    console.log('✅ Pino 传输器工作正常');
    return true;
  } catch (error) {
    console.error('❌ Pino 传输器测试失败:', error.message);
    return false;
  }
}

async function testSimplePrettyTerminalTransport() {
  console.log('\n🔧 测试 SimplePrettyTerminal 传输器...');
  
  try {
    const { SimplePrettyTerminalTransport } = require('@loglayer/transport-simple-pretty-terminal');
    
    const logger = new LogLayer({
      transport: new SimplePrettyTerminalTransport({
        colorize: true
      })
    });
    
    logger.info('SimplePrettyTerminal 传输器测试成功', { test: 'simplePrettyTerminal' });
    console.log('✅ SimplePrettyTerminal 传输器工作正常');
    return true;
  } catch (error) {
    console.error('❌ SimplePrettyTerminal 传输器测试失败:', error.message);
    return false;
  }
}

async function testRedactionPlugin() {
  console.log('\n🔧 测试 Redaction 插件...');
  
  try {
    const { redactionPlugin } = require('@loglayer/plugin-redaction');
    const { ConsoleTransport } = require('loglayer');
    
    const logger = new LogLayer({
      transport: new ConsoleTransport({
        logger: console
      }),
      plugins: [
        redactionPlugin({
          paths: ['password', 'token'],
          censor: '[REDACTED]'
        })
      ]
    });
    
    logger.info('Redaction 插件测试', { 
      username: 'testuser',
      password: 'secret123',
      token: 'abc123xyz',
      data: 'public'
    });
    console.log('✅ Redaction 插件工作正常');
    return true;
  } catch (error) {
    console.error('❌ Redaction 插件测试失败:', error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 LogLayer 传输器测试开始\n');
  
  const results = [];
  
  // 测试各个传输器
  results.push(await testConsoleTransport());
  results.push(await testWinstonTransport());
  results.push(await testPinoTransport());
  results.push(await testSimplePrettyTerminalTransport());
  results.push(await testRedactionPlugin());
  
  // 统计结果
  const passed = results.filter(r => r).length;
  const total = results.length;
  
  console.log(`\n📊 测试结果: ${passed}/${total} 通过`);
  
  if (passed === total) {
    console.log('🎉 所有传输器测试通过！');
    process.exit(0);
  } else {
    console.log('❌ 部分传输器测试失败');
    process.exit(1);
  }
}

// 运行测试
main().catch(console.error);
