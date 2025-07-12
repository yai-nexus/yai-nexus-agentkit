import { 
  CopilotRuntime, 
  copilotRuntimeNextJSAppRouterEndpoint,
  CopilotServiceAdapter
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
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
    this.httpAgent = new HttpAgent({
      url: backendUrl,
      description: "YAI Nexus Agent for AG-UI protocol"
    });
    this.options = options;
    
    // 使用注入的 logger，添加 fekit 上下文
    this.baseLogger = options.logger.child({ component: 'yai-nexus-fekit' });
  }
  
  /**
   * 创建带有请求上下文的 logger
   */
  private createRequestLogger(context: { traceId?: string; runId?: string; threadId?: string }): Logger {
    return this.baseLogger.child(context);
  }

  private generateTraceId(): string {
    if (this.options.tracing?.generateTraceId) {
      return this.options.tracing.generateTraceId();
    }
    // 默认生成策略：trace_ + 时间戳 + 随机数
    return `trace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async process(request: any): Promise<any> {
    // 生成或使用现有的追踪 ID
    const traceId = this.options.tracing?.enabled ? this.generateTraceId() : undefined;
    const threadId = request.threadId || traceId || 'default';
    const runId = request.runId || `run_${Date.now()}`;

    // Since HttpAgent expects RunAgentInput format, we need minimal conversion
    const agentInput = {
      threadId,
      runId,
      messages: request.messages || [],
      tools: request.tools || [],
      context: [],
      state: request.state || null,
    };

    // 创建请求级别的 logger
    const requestLogger = this.createRequestLogger({ traceId, runId, threadId });
    
    // 记录请求开始
    if (traceId) {
      requestLogger.info("Processing non-streaming request", { 
        operation: "process",
        messageCount: request.messages?.length || 0
      });
    }

    // Use HttpAgent's runAgent method for non-streaming
    await this.httpAgent.runAgent(agentInput);
    
    // For now, return a simple response
    // The HttpAgent handles the AG-UI protocol internally
    return {
      id: `response_${Date.now()}`,
      content: "Response from YAI Nexus backend",
      role: "assistant"
    };
  }

  async *stream(request: any): AsyncIterable<any> {
    // 生成或使用现有的追踪 ID
    const traceId = this.options.tracing?.enabled ? this.generateTraceId() : undefined;
    const threadId = request.threadId || traceId || 'default';
    const runId = request.runId || `run_${Date.now()}`;

    // Since HttpAgent expects RunAgentInput format, we need minimal conversion
    const agentInput = {
      threadId,
      runId,
      messages: request.messages || [],
      tools: request.tools || [],
      context: [],
      state: request.state || null,
    };

    // 创建请求级别的 logger
    const requestLogger = this.createRequestLogger({ traceId, runId, threadId });
    
    // 记录流式请求开始
    if (traceId) {
      requestLogger.info("Processing streaming request", { 
        operation: "stream",
        messageCount: request.messages?.length || 0
      });
    }

    // Use HttpAgent's run method for streaming
    const events$ = this.httpAgent.run(agentInput);
    
    // Convert Observable to AsyncIterable
    yield* this.observableToAsyncIterable(events$);
  }

  private async *observableToAsyncIterable(observable: any): AsyncIterable<any> {
    const chunks: any[] = [];
    let completed = false;
    let error: any = null;

    const subscription = observable.subscribe({
      next: (chunk: any) => chunks.push(chunk),
      error: (err: any) => { error = err; },
      complete: () => { completed = true; }
    });

    try {
      while (!completed && !error) {
        if (chunks.length > 0) {
          const chunk = chunks.shift();
          // Convert AG-UI events to CopilotKit format
          yield {
            type: 'content',
            content: chunk.type || 'event',
            data: chunk
          };
        } else {
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      }

      if (error) throw error;

      // Process remaining chunks
      while (chunks.length > 0) {
        const chunk = chunks.shift();
        yield {
          type: 'content', 
          content: chunk.type || 'event',
          data: chunk
        };
      }
    } finally {
      subscription.unsubscribe();
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
  const serviceAdapter = new YaiNexusServiceAdapter(options.backendUrl, options);

  // Create CopilotRuntime
  const runtime = new CopilotRuntime({
    middleware: {
      onBeforeRequest: async ({ threadId, runId, inputMessages, properties }) => {
        const logger = serviceAdapter.baseLogger.child({ 
          threadId, 
          runId, 
          phase: 'before' 
        });
        logger.info("CopilotRuntime request started", {
          messageCount: inputMessages.length,
          properties
        });
      },
      onAfterRequest: async ({ threadId, runId, inputMessages, outputMessages, properties }) => {
        const logger = serviceAdapter.baseLogger.child({ 
          threadId, 
          runId, 
          phase: 'after' 
        });
        logger.info("CopilotRuntime request completed", {
          inputCount: inputMessages.length,
          outputCount: outputMessages.length,
          properties
        });
      }
    }
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
        error: error instanceof Error ? {
          name: error.name,
          message: error.message,
          stack: error.stack
        } : { message: String(error) },
        url: req.url,
        method: req.method
      });
      
      // Return a proper error response
      return new Response(
        JSON.stringify({
          error: 'Internal server error',
          message: error instanceof Error ? error.message : 'Unknown error',
        }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
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