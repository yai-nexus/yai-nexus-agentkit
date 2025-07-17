# @yai-nexus/fekit

`@yai-nexus/fekit` 是一个与 `@yai-nexus/agentkit` 配套的前端开发工具包，旨在帮助您轻松地将强大的 AI Agent 功能集成到您的 React/Next.js 应用中。它通过提供一组高阶组件和 API 处理器，极大地简化了前后端的通信和状态管理。

## 🌟 核心特性

- **无缝集成 Next.js**: 提供专为 Next.js App Router 设计的 API Route Handler，轻松连接前端与您的 Python Agent 后端。
- **React 优先**: 以 React 组件和 Hooks 为核心，提供声明式的、富有表现力的 API。
- **状态管理内置**: 内置了对会话状态、消息历史等的管理，无需您手动处理复杂的状态逻辑。
- **协议兼容**: 完全兼容 AG-UI 协议，能够直接消费由 `@yai-nexus/agentkit` 的 `AGUIAdapter` 生成的事件流。

## 💿 安装

```bash
pnpm add @yai-nexus/fekit
```

## 🚀 快速上手

将 `fekit` 集成到您的 Next.js 应用中通常只需要两个步骤：

### 1. 创建后端 API 路由

在您的 Next.js 项目中，创建一个 API 路由（例如 `app/api/copilotkit/route.ts`），它将作为前端与 Python Agent 后端之间的代理。

```typescript
// app/api/copilotkit/route.ts
import { copilotkitHandler } from "@yai-nexus/fekit";

// `copilotkitHandler` 会将所有请求转发到您在环境变量中
// 定义的 AGENT_KIT_URL (例如 http://localhost:8000/api/chat)
export const POST = copilotkitHandler;
```

您需要在您的环境变量文件 (`.env.local`) 中指定后端 Agent 的地址：
```
AGENT_KIT_URL="http://localhost:8000/api/chat"
```

### 2. 在前端包裹您的应用

使用 `CopilotKit` 组件包裹您的应用或需要使用 AI 功能的页面。

```tsx
// components/ClientProviders.tsx
"use client";

import { CopilotKit } from "@yai-nexus/fekit";
import "@copilotkit/react-ui/styles.css"; // 引入 UI 样式

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    // 指定您的 API 路由地址
    <CopilotKit url="/api/copilotkit">
      {children}
    </CopilotKit>
  );
}
```

然后，在您的根 `layout.tsx` 中使用这个 Provider：
```tsx
// app/layout.tsx
import { ClientProviders } from "@/components/ClientProviders";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
```

### 3. 使用 UI 组件（可选）

`fekit` 与 `@copilotkit/react-ui` 兼容。您可以在页面中直接使用其提供的 UI 组件。

```tsx
// app/page.tsx
import { CopilotPopup } from "@copilotkit/react-ui";

export default function HomePage() {
  return (
    <div>
      <h1>欢迎使用 AgentKit!</h1>
      <CopilotPopup />
    </div>
  );
}
```

现在，您的应用已经成功集成了 `fekit`！前端的 CopilotKit 组件会通过 `/api/copilotkit` 路由与您的 Python 后端进行通信。

## 🤝 贡献

我们欢迎任何形式的社区贡献。请在提交 Pull Request 前，确保代码通过了格式化和 lint 检查。 