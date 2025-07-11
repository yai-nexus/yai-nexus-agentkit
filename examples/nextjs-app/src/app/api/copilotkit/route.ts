import { createYaiNexusHandler } from "@yai-nexus/fekit/server";
import { logger } from "@/lib/logger";

// 记录服务启动信息
logger.info("Initializing CopilotKit handler", {
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
    generateTraceId: () => `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  },
});

// 包装原始 handler 以添加我们的日志
const wrappedHandler = async (request: Request) => {
  const startTime = Date.now();
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  
  // 尝试从请求体中提取 thread_id 或 run_id 作为追踪信息
  let traceInfo = {};
  try {
    if (request.method === 'POST') {
      const clonedRequest = request.clone();
      const body = await clonedRequest.json();
      if (body.threadId || body.runId) {
        traceInfo = {
          threadId: body.threadId,
          runId: body.runId,
          messageCount: body.messages?.length || 0
        };
      }
    }
  } catch (e) {
    // 忽略解析错误
  }
  
  logger.info("Processing CopilotKit request", {
    requestId,
    url: request.url,
    method: request.method,
    timestamp: new Date().toISOString(),
    ...traceInfo
  });
  
  try {
    const response = await handler(request);
    const duration = Date.now() - startTime;
    
    logger.info("CopilotKit request completed", {
      requestId,
      status: response.status,
      statusText: response.statusText,
      duration: `${duration}ms`,
      ...traceInfo
    });
    
    return response;
  } catch (error) {
    const duration = Date.now() - startTime;
    logger.error("CopilotKit request failed", {
      requestId,
      error: error instanceof Error ? error.message : 'Unknown error',
      duration: `${duration}ms`,
      ...traceInfo
    });
    throw error;
  }
};

export const POST = wrappedHandler;