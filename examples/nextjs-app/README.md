# Next.js 全栈 AI 应用示例

本项目是 **YAI Nexus AgentKit** 的旗舰示例（Flagship Example），旨在全面展示如何构建一个集成了后端 AI Agent、前端 React 组件和标准化日志系统的现代化全栈应用。

## 🌟 功能亮点

- **全栈集成**: 演示了前端 `Next.js` 应用如何通过 `@yai-nexus/fekit` 与 `python-backend` 服务进行无缝通信。
- **AI UI 组件**: 集成了 [CopilotKit](https://www.copilotkit.ai/)，展示如何快速构建丰富的 AI 驱动的用户界面。
- **标准化日志**: 实现了 `@yai-nexus/loglayer-support` 在 Next.js 环境下的最佳实践，提供统一的、可靠的前后端日志记录。
- **现代化技术栈**: 使用 Next.js 14+, React, Tailwind CSS。

## 🚀 如何运行

**重要提示**: 请不要单独在此目录运行 `pnpm dev`。为了确保后端 Python 服务可用，您必须使用项目根目录下的统一脚本来启动。

1.  **确保依赖已安装**
    在 **项目根目录** 运行：
    ```bash
    pnpm install
    ```

2.  **启动所有服务**
    在 **项目根目录** 运行：
    ```bash
    ./scripts/services.sh start
    ```

3.  **访问应用**
    - **前端应用**: [http://localhost:3000](http://localhost:3000)
    - **后端服务**: [http://localhost:8000](http://localhost:8000)

您可以使用 `./scripts/services.sh status` 查看服务状态，或用 `./scripts/services.sh stop` 停止所有服务。

## 📂 代码结构导览

`src` 目录包含了本示例的核心逻辑：

- `src/app/api/copilotkit/route.ts`:
  这是前端与后端 AI Agent 通信的代理。它接收来自 CopilotKit 前端组件的请求，并将其转发到 `python-backend` 服务。

- `src/app/api/logging-demo/route.ts`:
  一个简单的 API 路由，用于演示 `loglayer-support` 如何在服务端捕获和记录日志。

- `src/lib/logger.ts`:
  `@yai-nexus/loglayer-support` 的实例化文件。这里使用 `createNextjsLoggerSync` 创建了一个与 Next.js 完全兼容的 logger 实例，供整个应用使用。

- `src/components/ClientProviders.tsx`:
  封装了所有客户端侧的 Provider，包括 CopilotKit 的 `CopilotKit` 和用于主题切换的 `ThemeProvider`。

- `src/app/page.tsx`:
  应用主页面，您可以在这里看到 CopilotKit UI 组件的实际使用。

## 🤝 贡献

欢迎通过提交 Issue 或 Pull Request 来改进此示例。
