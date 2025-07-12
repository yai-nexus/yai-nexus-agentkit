/**
 * SLS 日志集成演示 API
 * 
 * 演示如何在 Next.js API 路由中使用新的统一日志系统：
 * - 自动 SLS 上报（生产环境）
 * - 请求追踪 ID
 * - 结构化日志
 * - 错误记录
 */

import { NextRequest, NextResponse } from 'next/server';
import { logger, generateRequestId, generateTraceId } from '@/lib/logger';

export async function GET(request: NextRequest) {
  const requestId = generateRequestId();
  const traceId = generateTraceId();
  
  // 为此请求创建专门的 logger
  const reqLogger = logger.forRequest(requestId, traceId);
  
  const startTime = Date.now();
  
  try {
    reqLogger.info('API request started', {
      method: request.method,
      url: request.url,
      userAgent: request.headers.get('user-agent'),
    });

    // 模拟一些业务逻辑
    await simulateWork(reqLogger);
    
    // 模拟一些结构化日志
    reqLogger.info('Processing user data', {
      userId: 'demo_user_123',
      action: 'get_profile',
      timestamp: new Date().toISOString()
    });

    const duration = Date.now() - startTime;
    
    reqLogger.logPerformance('api_logging_demo', duration, {
      success: true,
      recordsProcessed: 42
    });

    reqLogger.info('API request completed successfully', {
      duration: `${duration}ms`,
      status: 200
    });

    return NextResponse.json({
      success: true,
      message: 'Logging demonstration completed',
      requestId,
      traceId,
      duration: `${duration}ms`,
      logs: {
        environment: process.env.NODE_ENV,
        slsEnabled: !!(process.env.SLS_ENDPOINT && process.env.SLS_PROJECT),
        features: {
          structuredLogging: true,
          requestTracing: true,
          performanceMetrics: true,
          cloudLogging: process.env.NODE_ENV === 'production'
        }
      }
    });

  } catch (error) {
    const duration = Date.now() - startTime;
    
    reqLogger.logError(error as Error, {
      requestId,
      traceId,
      duration: `${duration}ms`,
      endpoint: '/api/logging-demo'
    });

    return NextResponse.json({
      success: false,
      error: 'Internal server error',
      requestId,
      traceId
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const requestId = generateRequestId();
  const traceId = generateTraceId();
  const reqLogger = logger.forRequest(requestId, traceId);
  
  try {
    const body = await request.json();
    
    reqLogger.info('POST request received', {
      bodyKeys: Object.keys(body),
      contentType: request.headers.get('content-type')
    });

    // 演示错误日志记录
    if (body.simulateError) {
      throw new Error('Simulated error for logging demonstration');
    }

    // 演示不同级别的日志
    reqLogger.debug('Debug information', { debugData: 'sensitive-info' });
    reqLogger.warn('Warning message', { warningCode: 'DEMO_WARNING' });
    
    // 演示用户操作日志
    if (body.userId) {
      const userLogger = reqLogger.forUser(body.userId);
      userLogger.info('User action logged', {
        action: body.action || 'unknown',
        metadata: body.metadata || {}
      });
    }

    return NextResponse.json({
      success: true,
      message: 'POST logging demonstration completed',
      requestId,
      traceId,
      processedData: {
        keys: Object.keys(body),
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    reqLogger.logError(error as Error, {
      requestId,
      traceId,
      endpoint: '/api/logging-demo',
      method: 'POST'
    });

    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId,
      traceId
    }, { status: 500 });
  }
}

/**
 * 模拟一些异步工作
 */
async function simulateWork(reqLogger: ReturnType<typeof logger.forRequest>): Promise<void> {
  const workLogger = reqLogger.forModule('business-logic');
  
  workLogger.debug('Starting simulated work');
  
  // 模拟数据库查询
  await new Promise(resolve => setTimeout(resolve, 50));
  workLogger.info('Database query completed', {
    query: 'SELECT * FROM users',
    duration: '50ms',
    rows: 10
  });
  
  // 模拟外部 API 调用
  await new Promise(resolve => setTimeout(resolve, 30));
  workLogger.info('External API call completed', {
    api: 'https://api.example.com/data',
    duration: '30ms',
    status: 200
  });
  
  workLogger.debug('Simulated work completed');
}