# YAI Nexus FeKit

Yai Nexus FeKit (Frontend Kit) 是一个前端软件开发工具包（SDK），旨在简化与 YAI Nexus AI 代理后端的集成。它基于 [CopilotKit](https://www.copilotkit.ai/) 构建，并提供了一套完整的解决方案，用于在您的 Web 应用中快速实现功能强大的 AI 聊天助手。

## ✨ 功能特性

*   **无缝集成**: 提供简单的 React Provider (`YaiNexusPersistenceProvider`)，轻松集成到现有的 Next.js 应用中。
*   **本地持久化**: 利用 IndexedDB 自动在浏览器中保存和加载聊天记录，提升用户体验。
*   **后端通信**: 封装了与 YAI Nexus Python 后端的通信逻辑，实现了 AG-UI 协议。
*   **C/S 分离**: 提供了客户端 (`@yai-nexus/fekit/client`) 和服务器端 (`@yai-nexus/fekit/server`) 的明确分离，使代码结构更清晰。
*   **完整的示例**: 提供了一个包含 Next.js 前端和 Python (FastAPI) 后端的完整示例，帮助您快速上手。

## 📂 项目结构

本项目采用 pnpm workspace 管理的 monorepo 结构：

```
.
├── packages/
│   └── yai-nexus-fekit/   # 核心 SDK 包
├── examples/
│   ├── nextjs-app/        # Next.js 前端示例应用
│   └── python-backend/    # Python (FastAPI) 后端示例服务
└── ...
```

*   **`packages/yai-nexus-fekit`**: 核心库，可作为 npm 包发布和使用。
*   **`examples/nextjs-app`**: 一个完整的 Next.js 示例，演示了如何使用 `@yai-nexus/fekit` SDK。
*   **`examples/python-backend`**: 一个兼容的 Python 后端示例，用于与前端应用进行交互。

## 🚀 快速上手

请按照以下步骤在本地运行示例项目。

### 环境准备

*   Node.js (v18 或更高版本)
*   pnpm
*   Python (v3.9 或更高版本)

### 安装与运行

1.  **克隆仓库**
    ```bash
    git clone https://github.com/YAI-Nexus/yai-nexus-fekit.git
    cd yai-nexus-fekit
    ```

2.  **安装依赖**
    在项目根目录运行以下命令，安装所有工作区的依赖项：
    ```bash
    pnpm install
    ```

3.  **构建核心 SDK**
    构建 `@yai-nexus/fekit` 包：
    ```bash
    pnpm --filter @yai-nexus/fekit build
    ```

4.  **运行 Python 后端服务**
    打开一个新的终端，进入 Python 后端目录，创建并激活虚拟环境，然后启动服务：
    ```bash
    cd examples/python-backend

    # 创建虚拟环境
    python -m venv .venv

    # 激活虚拟环境 (macOS/Linux)
    source .venv/bin/activate
    # 或者 (Windows)
    # .\.venv\Scripts\activate

    # 安装 Python 依赖
    pip install -r requirements.txt

    # 启动后端服务
    python main.py
    ```
    服务将运行在 `http://localhost:8000`。

5.  **运行 Next.js 前端应用**
    回到项目根目录，在另一个终端中运行以下命令来启动前端开发服务器：
    ```bash
    pnpm --filter nextjs-app dev
    ```
    应用将运行在 `http://localhost:3000`。

6.  **访问应用**
    打开浏览器并访问 [http://localhost:3000](http://localhost:3000)，您现在可以与 AI 助手进行交互了！

## 💡 如何使用

要在您自己的项目中使用此 SDK：

1.  **安装包**:
    ```bash
    pnpm add @yai-nexus/fekit
    ```

2.  **设置 API 路由**:
    在您的 Next.js 项目中，创建一个 API 路由 (例如 `src/app/api/copilotkit/route.ts`) 来处理与后端的通信：
    ```typescript
    // src/app/api/copilotkit/route.ts
    import { createYaiNexusHandler } from "@yai-nexus/fekit/server";

    const handler = createYaiNexusHandler({
      // 您的 YAI Nexus 后端地址
      backendUrl: process.env.PYTHON_BACKEND_URL || "http://127.0.0.1:8000/invoke",
    });

    export const POST = handler;
    ```

3.  **包裹您的应用**:
    在您的前端页面或布局中，使用 `YaiNexusPersistenceProvider` 和 `CopilotKit` 来包裹您的聊天组件：
    ```tsx
    // src/app/page.tsx
    import { CopilotKit } from "@copilotkit/react-core";
    import { CopilotChat } from "@copilotkit/react-ui";
    import { YaiNexusPersistenceProvider } from "@yai-nexus/fekit/client";

    export default function Home() {
      const userId = "some-unique-user-id";

      return (
        <CopilotKit runtimeUrl="/api/copilotkit">
          <YaiNexusPersistenceProvider userId={userId}>
            <CopilotChat />
          </YaiNexusPersistenceProvider>
        </CopilotKit>
      );
    }
    ```

## 🤝 贡献

我们欢迎任何形式的贡献！如果您有任何问题或建议，请随时提交 Issue 或 Pull Request。

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证。