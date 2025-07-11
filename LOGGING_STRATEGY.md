
# 统一日志方案设计文档

## 1. 目标

为了提升在 `yai-nexus-agentkit` monorepo 中进行开发和联调的效率，我们设计一套统一的日志系统。该系统旨在解决以下痛点：

*   **问题定位困难**：请求在前端 (`nextjs-app`)、中间件 (`fekit`) 和后端 (`python-backend`) 之间流转，当出现问题时，很难快速定位到具体是哪个环节出错。
*   **日志格式不一**：不同服务、不同语言（TypeScript/Python）的日志格式五花八门，难以进行统一的查看和分析。
*   **缺少关键上下文**：日志中往往缺少如用户ID、会话ID等关键业务上下文，使得调试过程异常繁琐。

本方案的目标是建立一个 **可追踪、标准化、可配置** 的日志系统。

## 2. 核心设计原则

### 2.1. 端到端的可追踪性 (Traceability)

为每一个独立的业务请求（例如：一次完整的聊天问答）分配一个全局唯一的 **追踪ID (Trace ID)**。这个ID将在请求的整个生命周期中（从浏览器发起 -> Next.js后端 -> Python服务 -> 返回响应）保持不变，并被包含在每一条相关的日志中。

### 2.2. 结构化的日志格式 (Structured Logging)

所有服务和模块都必须输出统一的、机器可读的 **JSON格式** 日志。这便于后续的日志收集、解析、查询和可视化。

**标准日志字段**:

```json
{
  "timestamp": "2023-10-27T10:00:00.123Z",
  "level": "INFO",
  "service": "nextjs-app",
  "traceId": "trace-xyz-123",
  "userId": "demo_user_12345",
  "conversationId": "default-chat-abc",
  "message": "Successfully processed agent request",
  "details": {
    "path": "/api/copilotkit/invoke",
    "method": "POST",
    "durationMs": 150
  }
}
```

*   `timestamp`: ISO 8601 格式的时间戳。
*   `level`: 日志级别 (e.g., `DEBUG`, `INFO`, `WARN`, `ERROR`)。
*   `service`: 日志来源的服务名称 (e.g., `nextjs-app`, `python-backend`, `fekit`)。
*   `traceId`: 全局追踪ID。
*   `userId` / `conversationId`: 业务上下文ID（如果可用）。
*   `message`: 日志核心信息。
*   `details`: 包含额外上下文的结构化对象 (e.g., 请求参数、错误堆栈)。

### 2.3. 分级与可配置性 (Level & Configurability)

*   支持 `DEBUG`, `INFO`, `WARN`, `ERROR` 等标准日志级别。
*   每个服务的日志级别应可通过环境变量进行配置，以便在生产环境和开发环境之间切换。例如，`LOG_LEVEL=debug` 可以开启更详细的日志输出。

## 3. 技术实施方案

### 3.1. 追踪ID (Trace ID) 的生成与传递

1.  **生成点**：**Trace ID** 应在请求进入系统的第一个服务端节点生成。在我们的架构中，这个节点是 `nextjs-app` 的API路由 (`/api/copilotkit/route.ts`)。
2.  **传递方式**：
    *   在 `nextjs-app` 内部，Trace ID 可以通过 `AsyncLocalStorage` (Node.js) 或类似的上下文传递机制在不同的函数调用中共享。
    *   当 `nextjs-app` 调用 `python-backend` 时，Trace ID 必须通过自定义的HTTP Header（例如 `X-Trace-ID`）进行传递。

### 3.2. 前端实现 (Next.js & FeKit)

*   **日志库**：推荐使用 `pino` 库，它性能高，并原生支持JSON格式和日志级别。
*   **实现步骤**：
    1.  在 `nextjs-app` 的 `src/app/api/copilotkit/route.ts` 中，创建一个 `pino` logger 实例。
    2.  为每个进入的请求生成一个 `traceId`。
    3.  在 `createYaiNexusHandler` 中，将 `traceId` 和 `logger` 实例传递下去。
    4.  修改 `fekit` 包，使其在 `fetch` 请求中自动添加 `X-Trace-ID` header（或FastAPI中间件期望的 `X-Request-ID`），将 `traceId` 传给Python后端。

### 3.3. 后端实现 (Python Backend)

*   **日志库**：采用 [yai-nexus-logger](https://github.com/yai-nexus/yai-nexus-logger)，这是一个专门为现代Python应用设计的、支持追踪ID和结构化日志的库。
*   **实现步骤**：
    1.  在 `python-backend` 的 `requirements.txt` 中添加 `yai-nexus-logger` 依赖。
    2.  在应用启动时，使用 `init_logging()` 初始化日志系统，并开启 Uvicorn 集成 (`LOG_UVICORN_INTEGRATION_ENABLED=true`)。
    3.  参考 `yai-nexus-logger` 的文档，添加一个 FastAPI 中间件，用于从请求头 (`X-Request-ID` 或 `X-Trace-ID`) 中提取或生成 `traceId`，并使用 `trace_context.set_trace_id()` 将其存入上下文。
    4.  在应用代码中，通过 `get_logger(__name__)` 获取 logger 实例并记录日志。日志将自动包含 `traceId`。

## 4. 后续步骤

1.  [ ] **`python-backend`改造**：
    *   [ ] 在 `requirements.txt` 中添加 `yai-nexus-logger`。
    *   [ ] 添加 FastAPI 中间件来处理 `traceId`。
    *   [ ] 在应用启动时调用 `init_logging()`。
2.  [ ] **`fekit`改造**：添加日志记录器支持和`X-Trace-ID`的转发能力。
3.  [ ] **`nextjs-app`改造**：集成`pino`，生成`traceId`，并传递给`fekit`。
4.  [ ] **更新文档**：在各个项目的 `README.md` 中说明如何配置和查看日志。 