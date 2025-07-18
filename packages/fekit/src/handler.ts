import { HttpAgent } from "@ag-ui/client";
import type { BaseEvent } from "@ag-ui/core";
import {
  CopilotRuntime,
  CopilotServiceAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
  type CopilotRuntimeChatCompletionRequest,
  type CopilotRuntimeChatCompletionResponse,
} from "@copilotkit/runtime";
import type { IEnhancedLogger } from "@yai-nexus/loglayer-support";
import { NextRequest } from "next/server";

/**
 * 将 AG-UI 事件格式转换为 CopilotKit/Vercel AI SDK 期望的格式
 *
 * 根据 Vercel AI SDK 文档，正确的流事件格式应该是：
 * - 文本增量事件: `0:string\n`
 * - 数据事件: `2:Array<JSONValue>\n`
 * - 错误事件: `3:string\n`
 *
 * 参考: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
 */
function convertAGUIEventToCopilotKit(
  event: BaseEvent,
  logger: IEnhancedLogger
): string | null {
  try {
    // 根据事件类型进行转换
    switch (event.type) {
      case "TEXT_MESSAGE_CHUNK":
        // 文本消息块事件 - 使用 Vercel AI SDK 的文本增量格式
        const textContent = (event as any).delta || "";
        if (textContent) {
          return `0:${JSON.stringify(textContent)}\n`;
        }
        return null;

      case "THINKING_TEXT_MESSAGE_START":
        // 思考开始事件
        return `0:${JSON.stringify("[思考开始]\n")}\n`;

      case "THINKING_TEXT_MESSAGE_END":
        // 思考结束事件
        return `0:${JSON.stringify("\n[思考结束]\n")}\n`;

      case "RUN_STARTED":
        // 运行开始事件 - 发送空文本
        return `0:${JSON.stringify("")}\n`;

      case "RUN_FINISHED":
        // 运行结束事件 - 发送空文本
        return `0:${JSON.stringify("")}\n`;

      case "TOOL_CALL_START":
        // 工具调用开始事件
        const toolStartEvent = event as any;
        const toolStartText = `[工具调用: ${toolStartEvent.tool_call_name}]\n`;
        return `0:${JSON.stringify(toolStartText)}\n`;

      case "TOOL_CALL_END":
        // 工具调用结束事件
        return `0:${JSON.stringify("[工具调用完成]\n")}\n`;

      case "TOOL_CALL_RESULT":
        // 工具调用结果事件
        const toolResultEvent = event as any;
        const resultText = `结果: ${toolResultEvent.content}\n`;
        return `0:${JSON.stringify(resultText)}\n`;

      default:
        // 未知事件类型，记录警告
        logger.warn("Unknown AG-UI event type for conversion", {
          eventType: event.type,
          eventData: event,
        });
        return null;
    }
  } catch (error) {
    logger.error("Error converting AG-UI event to CopilotKit format", {
      error: error instanceof Error ? error.message : String(error),
      eventType: event.type,
      eventData: event,
    });
    return null;
  }
}

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
      timestamp: new Date().toISOString(), // 测试热重载 - 添加时间戳
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
    // 🔍 添加方法入口日志
    this.baseLogger.info("[PROCESS_START] Method called", {
      timestamp: new Date().toISOString(),
      requestKeys: Object.keys(request),
      hasEventSource: !!request.eventSource,
      eventSourceType: typeof request.eventSource,
      messagesCount: request.messages?.length || 0,
      threadId: request.threadId,
      runId: request.runId,
    });

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

    requestLogger.info("[PROCESS_LOGGER_CREATED] Request logger initialized", {
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

      requestLogger.info("[EVENTSOURCE_CHECK] Checking for eventSource", {
        hasEventSource: !!request.eventSource,
        eventSourceType: typeof request.eventSource,
        eventSourceUndefined: request.eventSource === undefined,
        eventSourceNull: request.eventSource === null,
        eventSourceFalsy: !request.eventSource,
      });

      // 如果有 eventSource，我们可以尝试使用它来处理流式响应
      if (request.eventSource) {
        requestLogger.info(
          "[EVENTSOURCE_FOUND] EventSource detected, processing...",
          {
            eventSourceConstructor: request.eventSource.constructor?.name,
          }
        );

        requestLogger.info("EventSource detected, delegating stream handling", {
          eventSourceType: typeof request.eventSource,
          availableMethods: Object.getOwnPropertyNames(
            Object.getPrototypeOf(request.eventSource)
          ),
          hasStreamMethod: typeof request.eventSource.stream === "function",
          eventSourceKeys: Object.keys(request.eventSource),
          eventSourceConstructor: request.eventSource.constructor.name,
          eventSourcePrototype: Object.getPrototypeOf(request.eventSource)
            .constructor.name,
          eventSourceDescriptor: Object.getOwnPropertyDescriptor(
            request.eventSource,
            "stream"
          ),
          eventSourceStringified: JSON.stringify(request.eventSource, null, 2),
          allProperties: Object.getOwnPropertyNames(request.eventSource),
          allDescriptors: Object.getOwnPropertyNames(
            request.eventSource
          ).reduce((acc, key) => {
            acc[key] = Object.getOwnPropertyDescriptor(
              request.eventSource,
              key
            );
            return acc;
          }, {} as any),
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

        // 直接运行 HttpAgent 并处理流式响应
        requestLogger.info("Running HttpAgent directly", {
          agentInput: JSON.stringify(agentInput, null, 2),
          httpAgentUrl: this.httpAgent.url,
        });

        // 获取 HttpAgent 的事件流
        const events$ = this.httpAgent.run(agentInput);

        requestLogger.info("Got events observable from HttpAgent.run()", {
          observableType: typeof events$,
          hasSubscribe: typeof events$?.subscribe === "function",
          observableConstructor: events$?.constructor?.name,
        });

        // 如果有 eventSource，尝试将事件流传递给它
        if (
          request.eventSource &&
          typeof request.eventSource.stream === "function"
        ) {
          requestLogger.info("Using eventSource.stream to handle events");

          await request.eventSource.stream(async (eventStream$: any) => {
            requestLogger.info("Inside eventSource.stream callback", {
              eventStreamType: typeof eventStream$,
              eventStreamMethods: eventStream$
                ? Object.getOwnPropertyNames(
                    Object.getPrototypeOf(eventStream$)
                  )
                : [],
            });

            requestLogger.info(
              "🚀 [CRITICAL] About to subscribe to HttpAgent Observable"
            );
            console.log(
              "🚀 [CRITICAL] About to subscribe to HttpAgent Observable"
            );

            // 订阅 HttpAgent 的事件流并转发到 eventSource
            return new Promise<void>((resolve, reject) => {
              let eventCount = 0;

              const subscription = events$.subscribe({
                next: (event: BaseEvent) => {
                  eventCount++;
                  requestLogger.info("🎯 [NEW] Received event from HttpAgent", {
                    eventType: event.type,
                    eventData: event,
                    eventCount,
                    hasEventStream: !!eventStream$,
                    eventStreamNextType: typeof eventStream$?.next,
                  });

                  console.log(
                    `🎯 [NEW] Received event from HttpAgent - Type: ${event.type}, Count: ${eventCount}`
                  );

                  // 转发事件到 eventSource
                  if (eventStream$ && typeof eventStream$.next === "function") {
                    requestLogger.debug("Forwarding event to eventSource", {
                      eventType: event.type,
                      eventTimestamp: event.timestamp,
                    });

                    // 转换 AG-UI 事件格式为 CopilotKit 期望的格式
                    const copilotEventData = convertAGUIEventToCopilotKit(
                      event,
                      requestLogger
                    );

                    if (copilotEventData) {
                      eventStream$.next(copilotEventData);
                    } else {
                      requestLogger.warn("Failed to convert event, skipping", {
                        eventType: event.type,
                      });
                    }
                  } else {
                    requestLogger.warn(
                      "Cannot forward event - eventStream$ next not available",
                      {
                        hasEventStream: !!eventStream$,
                        eventStreamNextType: typeof eventStream$?.next,
                      }
                    );
                  }
                },
                complete: () => {
                  requestLogger.info(
                    "HttpAgent stream completed, completing eventSource stream",
                    {
                      totalEvents: eventCount,
                    }
                  );
                  if (
                    eventStream$ &&
                    typeof eventStream$.complete === "function"
                  ) {
                    eventStream$.complete();
                  }
                  resolve();
                },
                error: (error: any) => {
                  requestLogger.error("HttpAgent stream error", {
                    error: error.message,
                    stack: error.stack,
                    totalEvents: eventCount,
                  });
                  if (
                    eventStream$ &&
                    typeof eventStream$.error === "function"
                  ) {
                    eventStream$.error(error);
                  }
                  reject(error);
                },
              });

              requestLogger.info(
                "🔗 [CRITICAL] Subscription created successfully"
              );
              console.log("🔗 [CRITICAL] Subscription created successfully");

              // 添加超时保护
              const timeout = setTimeout(() => {
                requestLogger.warn("Observable subscription timeout", {
                  totalEvents: eventCount,
                });
                subscription.unsubscribe();
                resolve();
              }, 30000); // 30 秒超时

              subscription.add(() => {
                clearTimeout(timeout);
              });
            });
          });
        } else {
          // 如果没有 eventSource.stream，直接订阅事件流
          requestLogger.info(
            "No eventSource.stream available, subscribing directly"
          );

          await new Promise<void>((resolve, reject) => {
            let eventCount = 0;

            requestLogger.info(
              "🚀 [CRITICAL] About to subscribe to HttpAgent Observable (direct)"
            );
            console.log(
              "🚀 [CRITICAL] About to subscribe to HttpAgent Observable (direct)"
            );

            const subscription = events$.subscribe({
              next: (event: BaseEvent) => {
                eventCount++;
                requestLogger.info(
                  "🎯 [NEW] Received event from HttpAgent (direct)",
                  {
                    eventType: event.type,
                    eventData: event,
                    eventCount,
                  }
                );

                console.log(
                  `🎯 [NEW] Received event from HttpAgent (direct) - Type: ${event.type}, Count: ${eventCount}`
                );
              },
              complete: () => {
                requestLogger.info("HttpAgent stream completed (direct)", {
                  totalEvents: eventCount,
                });
                resolve();
              },
              error: (error: any) => {
                requestLogger.error("HttpAgent stream error (direct)", {
                  error: error.message,
                  stack: error.stack,
                  totalEvents: eventCount,
                });
                reject(error);
              },
            });

            requestLogger.info(
              "🔗 [CRITICAL] Direct subscription created successfully"
            );
            console.log(
              "🔗 [CRITICAL] Direct subscription created successfully"
            );

            // 添加超时保护
            const timeout = setTimeout(() => {
              requestLogger.warn("Observable subscription timeout (direct)", {
                totalEvents: eventCount,
              });
              subscription.unsubscribe();
              resolve();
            }, 30000); // 30 秒超时

            subscription.add(() => {
              clearTimeout(timeout);
            });
          });
        }
      } else {
        requestLogger.info(
          "[EVENTSOURCE_MISSING] No eventSource found, using fallback approach",
          {
            requestKeys: Object.keys(request),
            eventSourceValue: request.eventSource,
          }
        );
      }

      // 返回简化的响应 - 实际内容通过 eventSource 流式传输
      const response: CopilotRuntimeChatCompletionResponse = {
        threadId,
        runId,
        // 不包含具体的消息内容，因为这些通过 eventSource 流式传输
      };

      requestLogger.info(
        "[PROCESS_COMPLETE] Process method completed with simplified response",
        {
          response,
          executionTime: Date.now() - parseInt(runId.replace("run_", "")),
        }
      );

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
    delegateAgentProcessingToServiceAdapter: true,
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
      const response = await handleRequest(req);

      // 如果是流式响应，添加 Vercel AI SDK 兼容的头
      if (response.headers.get("content-type")?.includes("text/plain")) {
        response.headers.set("x-vercel-ai-data-stream", "v1");
      }

      return response;
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
