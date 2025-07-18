import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  type CopilotServiceAdapter,
  type CopilotRuntimeChatCompletionRequest,
  type CopilotRuntimeChatCompletionResponse,
} from "@copilotkit/runtime";
import type { IEnhancedLogger } from "@yai-nexus/loglayer-support";
import { NextRequest } from "next/server";

// 定义返回函数的类型，避免依赖内部类型
type HandlerFunction = (req: NextRequest, res?: any) => Promise<Response>;

/**
 * HttpAgent 的适配器包装器，实现 CopilotServiceAdapter 接口
 * 解决 HttpAgent 缺少 process 方法的问题
 * 
 * 此适配器将 CopilotKit 的运行时请求转换为 AG-UI 的格式，
 * 并通过 HttpAgent 与 Python 后端进行通信。
 */
class HttpAgentAdapter implements CopilotServiceAdapter {
  private logger: IEnhancedLogger;

  constructor(private httpAgent: HttpAgent, logger: IEnhancedLogger) {
    this.logger = logger.child({ component: "HttpAgentAdapter" });
  }

  async process(request: CopilotRuntimeChatCompletionRequest): Promise<CopilotRuntimeChatCompletionResponse> {
    this.logger.info("Processing CopilotKit request via HttpAgent", {
      threadId: request.threadId,
      runId: request.runId,
      messageCount: request.messages.length,
      actionCount: request.actions.length,
    });

    try {
      // 使用 HttpAgent 处理请求并流式传输事件
      await request.eventSource.stream(async (eventStream) => {
        try {
          // 将 CopilotKit 消息转换为 AG-UI 格式
          const lastUserMessage = request.messages
            .filter(msg => msg.isTextMessage() && msg.role === 'user')
            .pop();
          
          if (!lastUserMessage) {
            this.logger.warn("No user message found in request");
            return;
          }

          // 发送开始事件
          eventStream.sendTextMessageStart({
            messageId: `response-${Date.now()}`,
          });

          // 构造 HttpAgent 参数
          const agentResult = await this.httpAgent.runAgent({
            runId: request.runId || `run-${Date.now()}`,
            // 可以添加更多参数
          }, {
            // 订阅 HttpAgent 的事件
            onTextMessageContentEvent: (params) => {
              eventStream.sendTextMessageContent({
                messageId: params.event.messageId,
                content: params.textMessageBuffer,
              });
            },
            onTextMessageEndEvent: (params) => {
              eventStream.sendTextMessageEnd({
                messageId: params.event.messageId,
              });
            },
            onToolCallStartEvent: (params) => {
              eventStream.sendActionExecutionStart({
                actionExecutionId: params.event.toolCallId,
                actionName: "tool_call", // 默认工具名称
              });
            },
            onToolCallResultEvent: (params) => {
              eventStream.sendActionExecutionResult({
                actionExecutionId: params.event.toolCallId,
                actionName: "tool_call",
                result: params.event.content, // 使用 content 字段作为结果
              });
            },
          });

          this.logger.info("HttpAgent streaming completed", {
            threadId: request.threadId,
            runId: request.runId,
          });

        } catch (streamError) {
          this.logger.error("Error during HttpAgent streaming", {
            error: streamError instanceof Error ? streamError.message : String(streamError),
            threadId: request.threadId,
            runId: request.runId,
          });
          
          // 发送错误信息到聊天
          eventStream.sendTextMessageStart({
            messageId: `error-${Date.now()}`,
          });
          eventStream.sendTextMessageContent({
            messageId: `error-${Date.now()}`,
            content: "抱歉，处理您的请求时出现了错误。请稍后再试。",
          });
          eventStream.sendTextMessageEnd({
            messageId: `error-${Date.now()}`,
          });
        }
      });

      return {
        threadId: request.threadId || "default-thread",
        runId: request.runId,
      };

    } catch (error) {
      this.logger.error("Error processing request via HttpAgent", {
        error: error instanceof Error ? error.message : String(error),
        threadId: request.threadId,
        runId: request.runId,
      });
      
      // 重新抛出错误，让 CopilotKit 处理
      throw error;
    }
  }
}

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
export function createYaiNexusHandler(
  options: CreateYaiNexusHandlerOptions
): HandlerFunction {
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

  // 3. 创建 HttpAgent 适配器并用作默认的 ServiceAdapter
  //    这可以确保所有未明确指定 agent 的请求（例如内部建议）
  //    以及明确指定 agentId="python-agent" 的请求，
  //    都统一路由到 Python 后端。
  const httpAgentAdapter = new HttpAgentAdapter(httpAgent, logger);
  
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: httpAgentAdapter,
    endpoint: "/api/copilotkit", // 确保与前端 API 路由一致
  });

  // 4. 直接返回 handleRequest 函数
  return handleRequest as HandlerFunction;
}

/**
 * Type alias for the return type of createYaiNexusHandler
 */
export type YaiNexusHandler = ReturnType<typeof createYaiNexusHandler>;
