import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  copilotRuntimeNextJSAppRouterEndpoint,
  CopilotServiceAdapter,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import type { Logger } from "pino";

export interface CreateYaiNexusHandlerOptions {
  backendUrl: string;
  logger: Logger; // 必填：应用提供统一的 logger
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
  public baseLogger: Logger;

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
  }

  /**
   * 创建带有请求上下文的 logger
   */
  private createRequestLogger(context: {
    traceId?: string;
    runId?: string;
    threadId?: string;
  }): Logger {
    return this.baseLogger.child(context);
  }

  private generateTraceId(): string {
    if (this.options.tracing?.generateTraceId) {
      return this.options.tracing.generateTraceId();
    }
    // 默认生成策略：trace_ + 时间戳 + 随机数
    return `trace_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  async process(request: any): Promise<any> {
    // 生成或使用现有的追踪 ID
    const traceId = this.options.tracing?.enabled
      ? this.generateTraceId()
      : undefined;
    const threadId = request.threadId || traceId || "default";
    const runId = request.runId || `run_${Date.now()}`;

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

    // Since HttpAgent expects RunAgentInput format, we need minimal conversion
    const agentInput = {
      threadId,
      runId,
      messages: formattedMessages,
      tools: request.tools || [],
      context: request.context || [],
      state: request.state || null,
      forwardedProps: request.forwardedProps || {},
    };

    // 创建请求级别的 logger
    const requestLogger = this.createRequestLogger({
      traceId,
      runId,
      threadId,
    });

    // 记录请求开始
    if (traceId) {
      requestLogger.info("Processing non-streaming request", {
        operation: "process",
        messageCount: request.messages?.length || 0,
      });
    }

    // Use HttpAgent's runAgent method for non-streaming
    await this.httpAgent.runAgent(agentInput);

    // For now, return a simple response
    // The HttpAgent handles the AG-UI protocol internally
    return {
      id: `response_${Date.now()}`,
      content: "Response from YAI Nexus backend",
      role: "assistant",
    };
  }

  async *stream(request: any): AsyncIterable<any> {
    // 生成或使用现有的追踪 ID
    const traceId = this.options.tracing?.enabled
      ? this.generateTraceId()
      : undefined;
    const threadId = request.threadId || traceId || "default";
    const runId = request.runId || `run_${Date.now()}`;

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

    // Since HttpAgent expects RunAgentInput format, we need minimal conversion
    const agentInput = {
      threadId,
      runId,
      messages: formattedMessages,
      tools: request.tools || [],
      context: request.context || [],
      state: request.state || null,
      forwardedProps: request.forwardedProps || {},
    };

    // 创建请求级别的 logger
    const requestLogger = this.createRequestLogger({
      traceId,
      runId,
      threadId,
    });

    // 记录流式请求开始
    if (traceId) {
      requestLogger.info("Processing streaming request", {
        operation: "stream",
        messageCount: request.messages?.length || 0,
      });
    }

    // Use HttpAgent's run method for streaming
    const events$ = this.httpAgent.run(agentInput);

    // Convert Observable to AsyncIterable
    yield* this.observableToAsyncIterable(events$);
  }

  private async *observableToAsyncIterable(
    observable: any
  ): AsyncIterable<any> {
    const requestLogger = this.baseLogger.child({
      method: "observableToAsyncIterable",
    });

    try {
      requestLogger.info("Starting observable to async iterable conversion");

      // 使用 Promise 来处理 Observable
      const chunks: any[] = [];
      let completed = false;
      let error: any = null;

      const subscription = observable.subscribe({
        next: (chunk: any) => {
          requestLogger.debug("Received chunk from observable", {
            chunkType: chunk?.type,
          });
          chunks.push(chunk);
        },
        error: (err: any) => {
          requestLogger.error("Observable error", { error: err.message });
          error = err;
        },
        complete: () => {
          requestLogger.info("Observable completed");
          completed = true;
        },
      });

      try {
        let yieldedCount = 0;
        while (!completed && !error) {
          if (chunks.length > 0) {
            const chunk = chunks.shift();
            yieldedCount++;

            // Convert AG-UI events to CopilotKit format
            const copilotEvent = {
              type: "content",
              content: chunk?.type || "event",
              data: chunk,
            };

            requestLogger.debug("Yielding chunk", {
              yieldedCount,
              chunkType: chunk?.type,
              eventType: copilotEvent.type,
            });

            yield copilotEvent;
          } else {
            await new Promise((resolve) => setTimeout(resolve, 10));
          }
        }

        if (error) {
          requestLogger.error("Throwing observable error", {
            error: error.message,
          });
          throw error;
        }

        // Process remaining chunks
        while (chunks.length > 0) {
          const chunk = chunks.shift();
          yieldedCount++;

          const copilotEvent = {
            type: "content",
            content: chunk?.type || "event",
            data: chunk,
          };

          requestLogger.debug("Yielding remaining chunk", {
            yieldedCount,
            chunkType: chunk?.type,
          });

          yield copilotEvent;
        }

        requestLogger.info("Observable conversion completed", {
          totalYielded: yieldedCount,
        });
      } finally {
        subscription.unsubscribe();
      }
    } catch (err) {
      requestLogger.error("Error in observable conversion", {
        error: err instanceof Error ? err.message : String(err),
      });
      throw err;
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
