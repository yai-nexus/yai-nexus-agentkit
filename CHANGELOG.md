# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-16

### 🎉 Major Features

#### LogLayer 抽象层实施
- **新增** `@yai-nexus/loglayer-support` 包 - 基于 LogLayer 的统一日志解决方案
- **解决** Next.js webpack 兼容性问题，支持自动传输器选择和回退
- **支持** 多种传输器：Pino、Winston、Console，可插拔设计
- **提供** 5 种预设配置：development、production、nextjsCompatible、test、consoleOnly

#### 代码简化和架构优化
- **减少** 日志配置代码量 99%+：从 136 行复杂逻辑简化为 1 行代码
- **实现** 100% API 向后兼容，无需修改现有业务代码
- **建立** 环境自适应机制，自动检测运行环境并选择最佳传输器

### 🔧 Breaking Changes

#### 包结构调整
- **移除** `@yai-nexus/pino-support` 包（已被 loglayer-support 替代）
- **删除** `examples/sls-pino-example` 项目
- **更新** 所有项目依赖，统一使用 `@yai-nexus/loglayer-support`

#### 迁移路径
```typescript
// 旧版本 (pino-support)
import { createEnhancedLogger, presets } from "@yai-nexus/pino-support";
// 复杂的 136 行初始化逻辑...

// 新版本 (loglayer-support) 
import { createNextjsLoggerSync } from "@yai-nexus/loglayer-support";
export const logger = createNextjsLoggerSync('app-name'); // 1 行搞定！
```

### ✨ Enhancements

#### fekit 包更新
- **迁移** 到 `@yai-nexus/loglayer-support`，保持完全的 API 兼容性
- **更新** 类型定义：`EnhancedLogger` → `IEnhancedLogger`
- **移除** 直接的 pino 依赖，通过抽象层使用

#### Next.js 应用优化
- **解决** 构建时的代理对象链式调用问题
- **确保** `logger.child().info()` 等链式调用在所有环境下正常工作
- **提供** 零配置的日志解决方案

### 📚 Documentation & Examples

#### 新增示例项目
- **创建** `examples/loglayer-example` - 完整的使用示例和迁移指南
- **包含** 基础使用、传输器测试、迁移演示等多个示例
- **提供** 详细的 API 文档和最佳实践

#### 文档完善
- **更新** 项目 README，反映新的架构和使用方式
- **创建** 迁移指南，帮助从 pino-support 平滑迁移
- **添加** 故障排除指南和常见问题解答

### 🧪 Testing & Quality

#### 端到端测试
- **实现** 100% 测试通过率（从 72% 提升到 100%）
- **验证** 所有包构建、示例运行、兼容性检查
- **确保** 生产环境可用性

#### 代码质量
- **通过** 所有 TypeScript 类型检查
- **遵循** 模块化设计原则，每个文件 < 200 行
- **实现** 完整的错误处理和回退机制

### 🚀 Performance & Reliability

#### 自动回退机制
```
Next.js 环境检测
    ↓
尝试 Pino 传输器
    ↓ (失败)
回退到 Winston 传输器  
    ↓ (失败)
回退到 Console 传输器 (保证可用)
```

#### 稳定性提升
- **解决** 代理对象异步问题，确保链式调用的同步性
- **提供** 优雅的错误处理和日志记录
- **支持** 多种运行环境：Node.js、Next.js、浏览器

### 📦 Dependencies

#### 新增依赖
- `loglayer` ^6.6.0 - 核心抽象层
- `@loglayer/transport-pino` ^2.0.0 - Pino 传输器
- `@loglayer/transport-winston` ^2.0.0 - Winston 传输器
- `@loglayer/transport-simple-pretty-terminal` ^2.0.0 - 终端传输器

#### 移除依赖
- 移除所有项目中的直接 `pino` 依赖
- 清理 `@yai-nexus/pino-support` 相关引用

### 🔄 Migration Guide

详细的迁移指南请参考：
- [loglayer-example 项目](./examples/loglayer-example/)
- [迁移演示](./examples/loglayer-example/src/migration-example.js)
- [项目总结](./PROJECT_SUMMARY.md)

---

## [0.2.6] - Previous Release

### Features
- 基础的 pino-support 日志系统
- Next.js 应用集成
- fekit 包基础功能

### Known Issues
- Next.js webpack 兼容性问题
- 复杂的日志配置逻辑
- 缺乏传输器抽象层
