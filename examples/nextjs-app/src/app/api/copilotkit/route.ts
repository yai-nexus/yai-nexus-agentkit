import { generateTraceId, logger } from "@/lib/logger";
import { createYaiNexusHandler } from "@yai-nexus/fekit/server";

// 记录服务启动信息
logger.info("Initializing CopilotKit handler", {
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000",
  environment: process.env.NODE_ENV,
});

// 使用新的简化 API，只需要 backendUrl 和 logger
export const POST = createYaiNexusHandler({
  backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000",
  logger: logger, // 注入统一的 EnhancedLogger
});

// 现在 fekit 内部已经处理了所有的日志记录和追踪，
// 不需要手动包装器！
