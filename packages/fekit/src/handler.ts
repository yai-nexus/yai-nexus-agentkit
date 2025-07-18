import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import type { IEnhancedLogger } from "@yai-nexus/loglayer-support";
import { NextRequest } from "next/server";

// 定义返回函数的类型，避免依赖内部类型
type HandlerFunction = (req: NextRequest, res?: any) => Promise<Response>;


export interface CreateYaiNexusHandlerOptions {
  backendUrl: string;
  logger: IEnhancedLogger;
}


/**
 * Creates a Next.js API route handler that connects CopilotKit frontend
 * with yai-nexus-agentkit Python backend using AG-UI protocol
 *
 * @param options Configuration options for the handler
 * @returns Next.js POST handler function
 *
 * @example
 * ```typescript
 * // /src/app/api/copilotkit/route.ts
 * import { createYaiNexusHandler } from "@yai-nexus/fekit";
 * import { logger } from "@/lib/logger";
 *
 * export const POST = createYaiNexusHandler({
 *   backendUrl: process.env.PYTHON_BACKEND_URL!,
 *   logger, // 注入应用的统一 logger
 * });
 * ```
 */
export function createYaiNexusHandler(options: CreateYaiNexusHandlerOptions): HandlerFunction {
  // 1. 初始化 HttpAgent
  const httpAgent = new HttpAgent({
    url: options.backendUrl,
    description: "YAI Nexus Agent for AG-UI protocol",
  });

  // 添加 fekit 上下文的 logger
  const logger = options.logger.child({ component: "yai-nexus-fekit" });

  // 记录 HttpAgent 初始化信息
  logger.info("HttpAgent initialized", {
    backendUrl: options.backendUrl,
    httpAgentUrl: httpAgent.url,
    timestamp: new Date().toISOString(),
  });

  // 2. 将 HttpAgent 实例直接传递给 `agents` 属性
  //    "python-agent" 是前端在 useCopilotChat 中使用的 agentId
  const runtime = new CopilotRuntime({
    agents: {
      "python-agent": httpAgent,
    },
  });

  // 3. 使用官方推荐的 `copilotRuntimeNextJSAppRouterEndpoint`
  //    并传入 ExperimentalEmptyAdapter 作为占位符
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit", // 确保与前端 API 路由一致
  });

  // 4. 直接返回 handleRequest 函数，无需任何 try...catch 封装
  //    运行时内部已经处理了错误
  return handleRequest as HandlerFunction;
}

/**
 * Type alias for the return type of createYaiNexusHandler
 */
export type YaiNexusHandler = ReturnType<typeof createYaiNexusHandler>;
