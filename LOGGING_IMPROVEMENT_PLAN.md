# 日志体系改进方案

## 1. 背景与动机

当前项目的日志体系在不同模块间存在不一致性，这给开发调试和后期运维带来了挑战。

- **Python 后端 (`examples/python-backend`)**: 目前使用 `yai-nexus-logger`。虽然实现了基本功能，但在上下文追踪（如 `trace_id`）方面需要手动在每个日志点传递 `extra` 字典，代码冗余且容易遗漏。
- **TypeScript SDK (`packages/fekit`)**: 内部仅使用 `console.log`，缺乏日志级别、结构化和统一管理的能力。
- **Next.js 应用 (`examples/nextjs-app`)**: 已经展现了使用结构化日志的意图（`import { logger } from "@/lib/logger"`），但日志模块本身并未实现。

为了提升代码质量、简化调试流程并为生产环境的监控做好准备，我们亟需一套统一、高效、现代化的日志解决方案。

## 2. 核心目标

本次改进旨在达成以下目标：

1.  **标准化**: 在 Python 和 TypeScript/Node.js 技术栈中建立统一的日志规范和最佳实践。
2.  **结构化日志**: 所有日志默认以 JSON 格式输出（生产环境），方便机器解析、采集和分析（如 ELK, Loki, Datadog）。
3.  **上下文追踪**: 轻松实现全链路追踪，自动将 `trace_id`, `request_id` 等上下文信息注入到相关的所有日志中。
4.  **提升开发体验**: 在开发环境提供美观、带颜色、易于阅读的日志格式。
5.  **生产环境就绪**: 提供高性能、可配置的日志轮转、压缩和异步写入等生产级功能。

## 3. 技术选型

### 3.1. Python 端: `loguru`

**替换** `yai-nexus-logger`，选用 `loguru`。

**优势**:
- **零配置启动**: `from loguru import logger` 即可使用，极其简单。
- **强大的上下文支持**: 通过 `logger.bind()` 或 `logger.contextualize()` 可以轻松绑定全局或请求级别的上下文，完美解决 `trace_id` 的传递问题。
- **开箱即用的文件日志**: `logger.add("file.log", rotation, retention, compression)` 一行代码即可实现强大的文件轮转、保留和压缩策略。
- **出色的异常追踪**: ` @logger.catch` 和 `logger.exception()` 能提供带有变量值的、更丰富的堆栈信息，极大加速调试。
- **JSON 支持**: 内置 `serialize=True` 选项，轻松输出结构化日志。

### 3.2. TypeScript/Node.js 端: `pino`

为 `nextjs-app` 和 `fekit` 引入 `pino` 作为标准日志库。

**优势**:
- **极致性能**: `pino` 是目前 Node.js 生态中性能最高的日志库之一，对生产环境非常友好。
- **JSON 优先**: 核心设计就是输出结构化 JSON 日志。
- **子记录器 (Child Loggers)**: 类似于 `loguru` 的 `bind`，可以创建一个继承父级上下文的子记录器，非常适合为每个 HTTP 请求创建独立的日志上下文。
- **美化工具**: `pino-pretty` 可以在开发环境中将 JSON 日志格式化为易读的彩色输出。
- **庞大的生态**: 拥有丰富的插件和集成来支持各种传输（Transports）和框架。

## 4. 实施方案

### Phase 1: Python 后端 (`agentkit` & 示例)

1.  **添加依赖**: 在 `packages/agentkit/pyproject.toml` 的 `[project.dependencies]` 中添加 `loguru`。
2.  **创建核心日志模块**:
    -   在 `packages/agentkit/src/yai_nexus_agentkit/core/` 目录下创建 `logging.py`。
    -   此文件将导出一个预先配置好的 `logger` 实例。配置将根据环境变量区分开发（美化输出）和生产（JSON 输出）模式。
    ```python
    # src/yai_nexus_agentkit/core/logging.py (示例)
    import sys
    from loguru import logger

    # 移除默认 handler
    logger.remove()

    # 根据环境配置
    log_format = "{time} {level} {extra[trace_id]} {message}" # 可自定义
    if os.getenv("ENV") == "production":
        logger.add(sys.stderr, format=log_format, serialize=True, level="INFO")
    else:
        logger.add(sys.stderr, format=log_format, colorize=True, level="DEBUG")

    # 导出 logger
    # ...
    ```
3.  **重构示例应用**:
    -   修改 `examples/python-backend/main.py`。
    -   移除 `yai-nexus-logger` 的所有引用。
    -   导入并使用 `yai_nexus_agentkit.core.logging` 中的 `logger`。
    -   使用 `logger.bind(trace_id=...).info(...)` 或 FastAPI 中间件结合 `logger.contextualize()` 来实现请求追踪，替代原有的手动传递 `extra`。
4.  **清理依赖**: 从 `examples/python-backend/requirements.txt` 中移除 `yai-nexus-logger`。

### Phase 2: TypeScript/Node.js 端 (`nextjs-app`)

1.  **添加依赖**:
    -   在 `examples/nextjs-app/package.json` 的 `dependencies` 中添加 `"pino"`。
    -   在 `devDependencies` 中添加 `"pino-pretty"`。
2.  **创建日志模块**:
    -   在 `examples/nextjs-app/src/lib/` 目录下创建 `logger.ts` 文件。
    -   此文件将配置并导出一个 `pino` 实例。配置会判断 `NODE_ENV`，在 `development` 模式下使用 `pino-pretty`。
    ```typescript
    // src/lib/logger.ts (示例)
    import pino from 'pino';

    const logger = pino({
      level: process.env.LOG_LEVEL || 'info',
      transport: process.env.NODE_ENV !== 'production'
        ? {
            target: 'pino-pretty',
            options: {
              colorize: true,
            },
          }
        : undefined,
    });

    export { logger };
    ```
3.  **应用日志模块**:
    -   `examples/nextjs-app/src/app/api/copilotkit/route.ts` 中现有的 `logger` 导入将直接生效。
    -   在 `wrappedHandler` 中，可以使用 `const reqLogger = logger.child({ requestId, traceId });` 来为每个请求创建一个子记录器，后续所有 `reqLogger.info()` 调用都将自动包含这些字段。
4.  **SDK (`fekit`) 调整 (可选)**:
    -   `fekit` 作为一个库，应避免强制依赖某个日志库。当前使用 `console.log` 是合理的。
    -   可以在 `createYaiNexusHandler` 选项中增加一个可选的 `logger` 参数，允许调用方注入自己的 logger 实例，从而实现更灵活的日志集成。如果未提供，则继续使用 `console.log`。

## 5. 收益总结

- **一致性与标准化**: 所有模块遵循统一的日志最佳实践。
- **高效调试**: 结构化和上下文追踪让定位问题变得前所未有地简单。
- **代码简洁**: 消除了在各处手动传递 `trace_id` 的模板代码。
- **面向未来**: 为将来接入专业的日志监控和告警系统打下坚实基础。

## 6. 下一步

请评审此方案。若无异议，我将按照上述实施方案分阶段进行代码重构。 