import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  CopilotServiceAdapter,
  type CopilotRuntimeChatCompletionRequest,
  type CopilotRuntimeChatCompletionResponse,
} from "@copilotkit/runtime";
import type { IEnhancedLogger } from "@yai-nexus/loglayer-support";
import { NextRequest } from "next/server";

export interface CreateYaiNexusHandlerOptions {
  backendUrl: string;
  logger: IEnhancedLogger; // 必填：应用提供统一的 IEnhancedLogger
  tracing?: {
    enabled?: boolean;
    generateTraceId?: () => string;
  };
}

/**
 * Lightweight adapter that proxies requests to AG-UI HttpAgent
 * Uses dependency injection for logger to integrate with application's unified logging system
 */
class YaiNexusServiceAdapter implements CopilotServiceAdapter {
  private httpAgent: HttpAgent;
  private options: CreateYaiNexusHandlerOptions;
  public baseLogger: IEnhancedLogger;

  constructor(backendUrl: string, options: CreateYaiNexusHandlerOptions) {
    // 使用 /agui 端点，这个端点返回 AG-UI 对象而不是 SSE 流
    const aguiUrl = backendUrl.endsWith("/")
      ? `${backendUrl}agui`
      : `${backendUrl}/agui`;

    this.httpAgent = new HttpAgent({
      url: aguiUrl,
      description: "YAI Nexus Agent for AG-UI protocol",
    });
    this.options = options;

    // 使用注入的 logger，添加 fekit 上下文
    this.baseLogger = options.logger.child({ component: "yai-nexus-fekit" });

    // 记录 HttpAgent 初始化信息
    this.baseLogger.info("HttpAgent initialized", {
      backendUrl,
      aguiUrl,
      httpAgentUrl: this.httpAgent.url,
    });
  }

  /**
   * 创建带有请求上下文的 logger
   */
  private createRequestLogger(context: {
    traceId?: string;
    runId?: string;
    threadId?: string;
  }): IEnhancedLogger {
    return this.baseLogger.child(context);
  }

  private generateTraceId(): string {
    if (this.options.tracing?.generateTraceId) {
      return this.options.tracing.generateTraceId();
    }
    // 默认生成策略：trace_ + 时间戳 + 随机数
    return `trace_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  /**
   * 处理请求 - 方案二：极简化版本
   *
   * 假设 CopilotKit 的 eventSource 会自动处理流式响应，
   * process 方法只需要返回基本的响应元数据
   *
   * 注意：使用 any 类型是因为 CopilotRuntimeChatCompletionRequest 和
   * CopilotRuntimeChatCompletionResponse 类型没有从 @copilotkit/runtime 导出，
   * 但我们仍然正确实现了 CopilotServiceAdapter 接口
   */
  async process(
    request: CopilotRuntimeChatCompletionRequest
  ): Promise<CopilotRuntimeChatCompletionResponse> {
    // 生成或使用现有的追踪 ID
    const traceId = this.options.tracing?.enabled
      ? this.generateTraceId()
      : undefined;
    const threadId = request.threadId || traceId || "default";
    const runId = request.runId || `run_${Date.now()}`;

    // 创建请求级别的 logger
    const requestLogger = this.createRequestLogger({
      traceId,
      runId,
      threadId,
    });

    requestLogger.info("Processing request with simplified approach", {
      operation: "process_v2",
      messageCount: request.messages?.length || 0,
      hasEventSource: !!request.eventSource,
      eventSourceMethods: request.eventSource
        ? Object.getOwnPropertyNames(Object.getPrototypeOf(request.eventSource))
        : [],
    });

    try {
      // 🎯 方案二：让 eventSource 处理所有流式逻辑
      // process 方法只返回基本的响应元数据

      // 如果有 eventSource，我们可以尝试使用它来处理流式响应
      if (request.eventSource) {
        requestLogger.info("EventSource detected, delegating stream handling", {
          eventSourceType: typeof request.eventSource,
          availableMethods: Object.getOwnPropertyNames(
            Object.getPrototypeOf(request.eventSource)
          ),
        });

        // 格式化消息，确保每个消息都有 id 字段
        const formattedMessages = (request.messages || []).map(
          (msg: any, index: number) => ({
            id: msg.id || `msg_${Date.now()}_${index}`,
            role: msg.role,
            content: msg.content,
            ...(msg.name && { name: msg.name }),
            ...(msg.tool_calls && { tool_calls: msg.tool_calls }),
            ...(msg.tool_call_id && { tool_call_id: msg.tool_call_id }),
          })
        );

        // 准备 AG-UI 格式的输入
        const agentInput = {
          threadId,
          runId,
          messages: formattedMessages,
          tools: request.actions || [],
          context: [],
          state: null,
          forwardedProps: request.forwardedParameters || {},
        };

        // 尝试通过 eventSource 处理流式响应
        // 这里我们假设 eventSource 有某种方式来处理流式数据
        try {
          // 获取 HttpAgent 的事件流
          const events$ = this.httpAgent.run(agentInput);

          requestLogger.info(
            "Got events observable, attempting to integrate with eventSource",
            {
              observableType: typeof events$,
              hasSubscribe: typeof events$?.subscribe === "function",
            }
          );

          // 尝试将事件流传递给 eventSource（如果它支持的话）
          // 这是一个实验性的方法，可能需要根据实际的 eventSource API 调整
          if (typeof request.eventSource.stream === "function") {
            requestLogger.info(
              "EventSource has stream method, attempting to use it"
            );

            await request.eventSource.stream(async (eventStream$: any) => {
              requestLogger.info("Inside eventSource.stream callback");

              // 订阅 HttpAgent 的事件流并转发到 eventSource
              events$.subscribe({
                next: (event: any) => {
                  requestLogger.debug("Forwarding event to eventSource", {
                    eventType: event?.type,
                    hasContent: !!event?.content,
                  });

                  // 尝试将 AG-UI 事件转发到 CopilotKit 的事件流
                  if (eventStream$ && typeof eventStream$.next === "function") {
                    eventStream$.next(event);
                  }
                },
                complete: () => {
                  requestLogger.info(
                    "HttpAgent stream completed, completing eventSource stream"
                  );
                  if (
                    eventStream$ &&
                    typeof eventStream$.complete === "function"
                  ) {
                    eventStream$.complete();
                  }
                },
                error: (error: any) => {
                  requestLogger.error("HttpAgent stream error", {
                    error: error.message,
                  });
                  if (
                    eventStream$ &&
                    typeof eventStream$.error === "function"
                  ) {
                    eventStream$.error(error);
                  }
                },
              });
            });
          }
        } catch (streamError) {
          requestLogger.warn("Failed to integrate with eventSource stream", {
            error:
              streamError instanceof Error
                ? streamError.message
                : String(streamError),
          });
        }
      }

      // 返回简化的响应 - 实际内容通过 eventSource 流式传输
      const response = {
        threadId,
        runId,
        // 不包含具体的消息内容，因为这些通过 eventSource 流式传输
      };

      requestLogger.info("Process method completed with simplified response", {
        response,
      });

      return response;
    } catch (error) {
      requestLogger.error("Error in simplified process method", {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      });

      throw error;
    }
  }
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
export function createYaiNexusHandler(options: CreateYaiNexusHandlerOptions) {
  // Create lightweight service adapter that proxies to AG-UI HttpAgent
  const serviceAdapter = new YaiNexusServiceAdapter(
    options.backendUrl,
    options
  );

  // Create CopilotRuntime
  const runtime = new CopilotRuntime({
    middleware: {
      onBeforeRequest: async ({
        threadId,
        runId,
        inputMessages,
        properties,
      }) => {
        const logger = serviceAdapter.baseLogger.child({
          threadId,
          runId,
          phase: "before",
        });
        logger.info("CopilotRuntime request started", {
          messageCount: inputMessages.length,
          properties,
        });
      },
      onAfterRequest: async ({
        threadId,
        runId,
        inputMessages,
        outputMessages,
        properties,
      }) => {
        const logger = serviceAdapter.baseLogger.child({
          threadId,
          runId,
          phase: "after",
        });
        logger.info("CopilotRuntime request completed", {
          inputCount: inputMessages.length,
          outputCount: outputMessages.length,
          properties,
        });
      },
    },
  });

  // Create and return the Next.js POST handler
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter, // Use our lightweight adapter
    endpoint: "/api/copilotkit",
  });

  return async function POST(req: NextRequest) {
    try {
      return await handleRequest(req);
    } catch (error) {
      // 使用注入的 logger 记录错误
      serviceAdapter.baseLogger.error("Handler error", {
        error:
          error instanceof Error
            ? {
                name: error.name,
                message: error.message,
                stack: error.stack,
              }
            : { message: String(error) },
        url: req.url,
        method: req.method,
      });

      // Return a proper error response
      return new Response(
        JSON.stringify({
          error: "Internal server error",
          message: error instanceof Error ? error.message : "Unknown error",
        }),
        {
          status: 500,
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
    }
  };
}

/**
 * Type alias for the return type of createYaiNexusHandler
 */
export type YaiNexusHandler = ReturnType<typeof createYaiNexusHandler>;
