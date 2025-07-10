import { CopilotRuntime, copilotRuntimeNextJSAppRouterEndpoint } from "@copilotkit/runtime";
import { YaiNexusAdapter, YaiNexusAdapterConfig } from "./adapter";
import { NextRequest } from "next/server";

export interface CreateYaiNexusHandlerOptions {
  backendUrl: string;
  logging?: {
    enabled?: boolean;
    progressive?: boolean;
  };
}

/**
 * Creates a Next.js API route handler that connects CopilotKit frontend
 * with yai-nexus-agentkit Python backend through ag-ui-protocol
 * 
 * @param options Configuration options for the handler
 * @returns Next.js POST handler function
 * 
 * @example
 * ```typescript
 * // /src/app/api/copilotkit/route.ts
 * import { createYaiNexusHandler } from "@yai-nexus/fekit";
 * 
 * export const POST = createYaiNexusHandler({
 *   backendUrl: process.env.PYTHON_BACKEND_URL!,
 * });
 * ```
 */
export function createYaiNexusHandler(options: CreateYaiNexusHandlerOptions) {
  // Create YaiNexus adapter instance
  const serviceAdapter = new YaiNexusAdapter({
    backendUrl: options.backendUrl,
  });

  // Create CopilotRuntime instance
  const runtime = new CopilotRuntime({
    logging: {
      enabled: options.logging?.enabled ?? true,
      progressive: options.logging?.progressive ?? true,
      logger: {
        logRequest: (data) => {
          if (options.logging?.enabled) {
            console.log('[YaiNexus] Request:', JSON.stringify(data, null, 2));
          }
        },
        logResponse: (data) => {
          if (options.logging?.enabled) {
            console.log('[YaiNexus] Response:', JSON.stringify(data, null, 2));
          }
        },
        logError: (error) => {
          console.error('[YaiNexus] Error:', error);
        },
      },
    },
  });

  // Create and return the Next.js POST handler
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return async function POST(req: NextRequest) {
    try {
      return await handleRequest(req);
    } catch (error) {
      console.error('[YaiNexus] Handler error:', error);
      
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