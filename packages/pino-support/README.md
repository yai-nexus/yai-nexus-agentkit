# @yai-nexus/pino-support

统一的 Node.js/TypeScript 日志解决方案，提供同构配置和云服务集成。

## 功能特性

- 🔧 **统一配置接口**：与 yai-loguru-support 语义一致的配置体验
- 🌐 **同构设计**：自动检测环境（浏览器/Node.js/Next.js），智能启用功能
- 📁 **智能目录策略**：按小时/天自动分目录，与 Python 端保持一致的结构
- 🚀 **高性能异步**：批量处理、异步写入，不阻塞主线程
- 🛠 **TypeScript 原生**：完整的类型安全和智能提示
- 🌩️ **多云支持**：支持阿里云 SLS，架构可扩展
- 🔧 **框架无关**：兼容 Next.js、Express、Fastify 等

## 快速开始

```bash
npm install @yai-nexus/pino-support
```

### 1. 统一日志配置

```typescript
import { createLogger, createDevLogger, createProdLogger } from '@yai-nexus/pino-support';

// 自动配置（开发环境美化输出 + 文件，生产环境JSON + 文件）
const logger = createLogger({
  serviceName: 'my-service',
  level: 'info',
  console: { enabled: true, pretty: true },
  file: { enabled: true, strategy: 'hourly' }
});

// 便捷函数
const devLogger = createDevLogger('my-service');     // 开发环境
const prodLogger = createProdLogger('my-service');   // 生产环境

logger.info('应用启动', { version: '1.0.0' });
```

### 2. 同构日志（浏览器 + Node.js）

```typescript
import { createLogger, detectEnvironment } from '@yai-nexus/pino-support';

// 自动检测环境，智能配置
const logger = createLogger({ serviceName: 'my-app' });

// 在 Node.js 中：控制台 + 文件输出
// 在浏览器中：仅控制台输出（文件自动禁用）

const env = detectEnvironment();
console.log('环境信息:', env);
// { isBrowser: false, isNode: true, isNextJs: true, environment: 'node' }

logger.info('这条日志在任何环境都能正常工作');
```

### 3. Next.js 集成

```typescript
// lib/logger.ts
import { createDevLogger, createProdLogger } from '@yai-nexus/pino-support';

const logger = process.env.NODE_ENV === 'development'
  ? createDevLogger('nextjs-app')
  : createProdLogger('nextjs-app');

export { logger };

// API 路由中使用
// pages/api/users.ts
import { logger } from '@/lib/logger';

export default function handler(req, res) {
  const reqLogger = logger.child({ requestId: generateId() });
  reqLogger.info('API 请求开始', { method: req.method, url: req.url });
  
  // 处理业务逻辑...
  
  reqLogger.info('API 请求完成', { status: 200 });
  res.json({ success: true });
}
```

### 4. 阿里云 SLS 集成

```typescript
import { createLogger } from '@yai-nexus/pino-support';

// 方式一：配置对象方式
const logger = createLogger({
  serviceName: 'my-service',
  level: 'info',
  console: { enabled: true, pretty: false },
  file: { enabled: true, strategy: 'hourly' },
  cloud: {
    enabled: true,
    sls: {
      endpoint: 'cn-hangzhou.log.aliyuncs.com',
      accessKeyId: process.env.SLS_AK_ID!,
      accessKeySecret: process.env.SLS_AK_KEY!,
      project: 'my-project',
      logstore: 'my-logstore'
    }
  }
});

// 方式二：手动添加 SLS transport
import { SlsTransport } from '@yai-nexus/pino-support/sls';

const baseLogger = createLogger({ serviceName: 'my-service' });
const slsTransport = new SlsTransport({
  endpoint: 'cn-hangzhou.log.aliyuncs.com',
  accessKeyId: process.env.SLS_AK_ID!,
  accessKeySecret: process.env.SLS_AK_KEY!,
  project: 'my-project',
  logstore: 'my-logstore'
});

await slsTransport.start();
// 现在日志会同时输出到：控制台、文件、SLS
```

## 日志目录结构

与 Python 端保持一致的目录结构：

```
logs/
├── current -> 20241213-14          # 当前小时软链接
├── 20241213-14/                    # 按小时分目录
│   ├── README.md                   # 目录说明
│   ├── nextjs-app.log              # Next.js 应用日志
│   └── my-service.log              # 其他服务日志
└── 20241213-15/                    # 下一小时目录
    └── nextjs-app.log
```

## 配置接口

### LoggerConfig 类型定义

```typescript
interface LoggerConfig {
  serviceName: string;                    // 服务名称（必需）
  level?: 'debug' | 'info' | 'warn' | 'error';  // 日志级别
  console?: {
    enabled?: boolean;                    // 启用控制台输出
    pretty?: boolean;                     // 美化输出（开发模式）
  };
  file?: {
    enabled?: boolean;                    // 启用文件输出
    baseDir?: string;                     // 日志根目录
    strategy?: 'hourly' | 'daily';       // 目录策略
    maxSize?: number;                     // 文件最大大小
    maxFiles?: number;                    // 保留文件数量
  };
  cloud?: {
    enabled?: boolean;                    // 启用云端日志
    sls?: {                              // 阿里云 SLS 配置
      endpoint: string;
      accessKeyId: string;
      accessKeySecret: string;
      project: string;
      logstore: string;
      region?: string;
    };
  };
}
```

### 环境检测

```typescript
interface EnvironmentInfo {
  isBrowser: boolean;      // 是否浏览器环境
  isNode: boolean;         // 是否 Node.js 环境
  isNextJs: boolean;       // 是否 Next.js 环境
  environment: 'browser' | 'node' | 'unknown';
}
```

## 与 Python 版本对比

| 功能 | Python (yai-loguru-support) | Node.js (@yai-nexus/pino-support) |
|------|------------------------------|-------------------------------------|
| **配置函数** | `setup_logging()` | `createLogger()` |
| **便捷函数** | `setup_dev_logging()` | `createDevLogger()` |
| **目录策略** | `HourlyDirectoryStrategy` | `strategy: 'hourly'` |
| **SLS 集成** | `AliyunSlsSink` | `SlsTransport` |
| **环境检测** | ❌ | ✅ 同构支持 |
| **配置结构** | Python Dict | TypeScript Interface |

两个版本提供完全一致的配置语义，可以无缝切换。

## 环境变量

```bash
# 阿里云 SLS 配置
SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
SLS_AK_ID=your_access_key_id
SLS_AK_KEY=your_access_key_secret
SLS_PROJECT=your_project
SLS_LOGSTORE=your_logstore

# Node.js 环境配置
NODE_ENV=development                # 影响默认配置
LOG_LEVEL=info                      # 可选的日志级别覆盖
```

## 许可证

MIT