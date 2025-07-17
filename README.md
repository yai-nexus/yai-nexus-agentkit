# YAI Nexus AgentKit

[![CI/CD](https://img.shields.io/badge/CI/CD-Coming_Soon-blue.svg)](https://github.com/your-org/yai-nexus-agentkit/actions)
[![Code Coverage](https://img.shields.io/badge/Coverage-Coming_Soon-red.svg)](https://codecov.io/gh/your-org/yai-nexus-agentkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

YAI Nexus AgentKit 是一个全栈、多语言的 monorepo 开发工具包，旨在简化和加速 AI Agent 及相关前端应用程序的构建、测试和部署。

## 🌟 项目概述

在构建复杂的 AI 应用时，开发者常常需要在前端和后端之间进行大量的协调工作，并处理不同语言和框架带来的复杂性。YAI Nexus AgentKit 通过提供一套集成的、预配置的工具和库来解决这个问题：

- **统一的开发环境**: 使用 [Nx](https://nx.dev/) 和 [pnpm](https://pnpm.io/) 管理 monorepo，实现跨项目的依赖管理、任务运行和代码共享。
- **全栈解决方案**: 提供从后端 Agent (Python) 到前端界面 (React/Next.js) 的完整开发体验。
- **标准化的日志系统**: 内置可插拔的日志支持，方便调试和监控。
- **丰富的示例**: 提供多个即开即用的示例项目，帮助您快速上手。

## 核心组件

| 包名 | 语言 | 描述 |
| --- | --- | --- |
| 📦 `packages/agentkit` | Python | 用于构建、编排和管理 AI Agent 的核心 Python 框架。 |
| 📦 `packages/fekit` | TypeScript | 配套的前端开发工具包，用于轻松地将 AI Agent 集成到 React/Next.js 应用中。 |
| 📦 `packages/loglayer-support` | TypeScript | 为 TypeScript/JavaScript 项目提供统一的日志服务，支持多种传输后端。 |
| 📦 `packages/loguru-support` | Python | 为 Python 项目提供基于 Loguru 的标准化日志解决方案。 |

## 🚀 快速开始

### 1. 环境要求

在开始之前，请确保您的开发环境中安装了以下工具：

- [Node.js](https://nodejs.org/) (推荐 v18 或更高版本)
- [pnpm](https://pnpm.io/installation)
- [Python](https://www.python.org/downloads/) (推荐 v3.10 或更高版本)

### 2. 安装依赖

克隆本仓库后，在项目根目录运行以下命令以安装所有依赖项：

```bash
pnpm install
```

### 3. 运行所有服务

我们提供了一个方便的脚本来启动和管理所有示例服务（Next.js 应用和 Python 后端）。

```bash
./scripts/services.sh start
```

该命令会启动：
- **Next.js 前端应用**: 访问 [http://localhost:3000](http://localhost:3000)
- **Python 后端服务**: 访问 [http://localhost:8000](http://localhost:8000)

您可以使用 `stop`, `restart`, `status` 等命令来管理服务。详情请查看脚本内容。

## 📚 示例

我们强烈建议您从 `examples` 目录开始探索。每个示例都是一个独立的项目，展示了如何使用本工具包的不同功能。

- `examples/nextjs-app`: 一个完整的 Next.js 应用，集成了前端开发工具包和日志系统。
- `examples/python-backend`: 一个基础的 Python 后端服务，使用了 AgentKit 和日志支持。
- `examples/loglayer-example`: 演示如何在 Node.js 环境下单独使用 `loglayer-support`。
- `examples/loguru-example`: 演示如何在 Python 环境下单独使用 `loguru-support`。

## 🤝 贡献指南

我们欢迎任何形式的社区贡献！无论是报告问题、提交功能请求还是直接贡献代码。请在提交 Pull Request 前先阅读我们的贡献指南（即将推出）。

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。
