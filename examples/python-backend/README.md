# Python 后端 AI Agent 示例

本项目是一个基于 FastAPI 的 Python 后端服务，是 **YAI Nexus AgentKit** 全栈示例的核心组成部分。它为 `nextjs-app` 前端应用提供强大的 AI Agent 支持。

## 🌟 功能亮点

- **FastAPI 驱动**: 基于现代、高性能的 FastAPI 框架构建。
- **AgentKit 集成**: 深度集成了 `@yai-nexus/agentkit`，用于处理和响应来自前端的 AI 请求。
- **标准化日志**: 使用 `@yai-nexus/loguru-support` 实现结构化、生产就绪的日志记录。
- **服务于前端**: 作为 `nextjs-app` 的后端，共同构成一个完整的全栈 AI 应用。

## 🚀 如何运行

**重要提示**: 请不要单独在此目录运行 `python main.py`。为了确保与前端应用协同工作，您必须使用项目根目录下的统一脚本来启动。

1.  **确保依赖已安装**
    在 **项目根目录** 运行：
    ```bash
    pnpm install
    ```
    这会确保所有 Python 和 Node.js 依赖都被正确安装。

2.  **启动所有服务**
    在 **项目根目录** 运行：
    ```bash
    ./scripts/services.sh start
    ```

3.  **服务地址**
    - **后端 API 服务**: [http://localhost:8000](http://localhost:8000)
    - **API 文档 (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

您可以使用 `./scripts/services.sh status` 查看服务状态，或用 `./scripts/services.sh stop` 停止所有服务。

## 📂 代码结构导览

`main.py` 是本项目的核心文件。

- **FastAPI 应用初始化**:
  创建 FastAPI 应用实例，并挂载中间件。

- **日志配置**:
  配置 `loguru`，并可能集成云日志服务（如 `loguru-support` 所示）。

- **AI Agent 端点**:
  定义了关键的 API 端点（例如 `/api/chat`），它负责：
  1.  接收来自 `nextjs-app` 的请求。
  2.  使用 `agentkit` 的能力来处理该请求（例如，与一个或多个 LLM 进行交互）。
  3.  将 Agent 的响应流式传输回前端。

## 🤝 贡献

欢迎通过提交 Issue 或 Pull Request 来改进此示例。