import { createYaiNexusHandler } from "@yai-nexus/fekit/server";
import { generateTraceId, createApiLogger } from "@/lib/logger";

// 为 CopilotKit API 创建专用的记录器
const apiLogger = createApiLogger("/api/copilotkit");

// 记录服务启动信息
apiLogger.info("Initializing CopilotKit handler", {
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
  environment: process.env.NODE_ENV
});

// 使用新的依赖注入 API，直接传入统一的 logger
export const POST = createYaiNexusHandler({
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
  logger: apiLogger.raw, // 注入统一的 logger
  tracing: {
    enabled: true,
    generateTraceId: generateTraceId
  },
});

// 现在 fekit 内部已经处理了所有的日志记录和追踪，
// 不需要手动包装器！