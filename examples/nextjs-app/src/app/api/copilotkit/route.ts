import { createYaiNexusHandler } from "@yai-nexus/fekit/server";
import { generateRequestId, generateTraceId, createApiLogger } from "@/lib/logger";
import { NextRequest } from "next/server";

// 为 CopilotKit API 创建专用的记录器
const apiLogger = createApiLogger("/api/copilotkit");

// 记录服务启动信息
apiLogger.info("Initializing CopilotKit handler", {
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
  environment: process.env.NODE_ENV
});

const handler = createYaiNexusHandler({
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
  logging: {
    enabled: true,
    progressive: true,
  },
  tracing: {
    enabled: true,
    generateTraceId: generateTraceId
  },
});

/**
 * 包装原始 handler 以添加统一的日志记录和追踪
 */
const wrappedHandler = async (request: NextRequest) => {
  const startTime = Date.now();
  const requestId = generateRequestId();
  let traceId: string | undefined;
  
  // 创建请求级别的记录器
  let reqLogger = apiLogger.forRequest(requestId);
  
  try {
    // 尝试从请求体中提取 thread_id 或 run_id 作为追踪信息
    if (request.method === 'POST') {
      try {
        const clonedRequest = request.clone();
        const body = await clonedRequest.json() as Record<string, unknown>;
        
        // 使用现有的 traceId 或生成新的
        traceId = (body.threadId as string) || (body.runId as string) || generateTraceId();
        
        // 更新记录器以包含追踪信息
        reqLogger = reqLogger.child({ 
          traceId,
          threadId: body.threadId as string,
          runId: body.runId as string,
          messageCount: (body.messages as unknown[])?.length || 0
        });
        
      } catch (parseError) {
        // 如果解析失败，生成新的 traceId
        traceId = generateTraceId();
        reqLogger = reqLogger.child({ traceId });
        reqLogger.warn("Failed to parse request body", { 
          error: parseError instanceof Error ? parseError.message : 'Unknown error' 
        });
      }
    } else {
      traceId = generateTraceId();
      reqLogger = reqLogger.child({ traceId });
    }
    
    // 记录请求开始
    reqLogger.logRequest({
      method: request.method,
      url: request.url,
      headers: Object.fromEntries(request.headers.entries()),
    }, "CopilotKit request started");
    
    // 执行实际的请求处理
    const response = await handler(request);
    const duration = Date.now() - startTime;
    
    // 记录成功响应
    reqLogger.logResponse({
      status: response.status,
      statusText: response.statusText,
    }, duration, "CopilotKit request completed");
    
    // 记录性能指标
    reqLogger.logPerformance("copilotkit_request", duration, {
      success: true,
      method: request.method,
    });
    
    return response;
    
  } catch (error) {
    const duration = Date.now() - startTime;
    
    // 记录错误详情
    reqLogger.logError(
      error instanceof Error ? error : new Error(String(error)),
      {
        method: request.method,
        url: request.url,
        duration: `${duration}ms`,
      },
      "CopilotKit request failed"
    );
    
    // 记录性能指标（包含错误）
    reqLogger.logPerformance("copilotkit_request", duration, {
      success: false,
      method: request.method,
      errorType: error instanceof Error ? error.name : 'UnknownError',
    });
    
    throw error;
  }
};

export const POST = wrappedHandler;