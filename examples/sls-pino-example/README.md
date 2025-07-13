# SLS Pino 集成示例

这个示例演示如何使用 `@yai-nexus/pino-support` 包将 Pino 日志发送到阿里云 SLS (Simple Log Service)。

## 功能特性

- ✅ **统一日志配置**: 使用与 Python 端语义一致的配置接口
- ✅ **多重输出**: 控制台 + 本地文件 + 阿里云 SLS
- ✅ **同构设计**: 自动检测运行环境（Node.js/浏览器）
- ✅ **结构化日志**: 支持丰富的上下文信息和元数据
- ✅ **性能优化**: 异步批量发送，不阻塞主线程
- ✅ **错误处理**: 自动重试和优雅降级
- ✅ **目录策略**: 与 Python 端保持一致的小时级目录结构

## 环境要求

- Node.js 18+
- 阿里云 SLS 服务（需要创建项目和日志库）

## 快速开始

### 1. 安装依赖

```bash
cd examples/sls-pino-example
npm install
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 阿里云 SLS 配置
SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com  # 根据你的区域调整
SLS_AK_ID=your_access_key_id               # 阿里云 AccessKey ID
SLS_AK_KEY=your_access_key_secret          # 阿里云 AccessKey Secret
SLS_PROJECT=your_project_name              # SLS 项目名称
SLS_LOGSTORE=your_logstore_name            # SLS 日志库名称

# 可选配置
LOG_LEVEL=info                             # 日志级别
NODE_ENV=development                       # 环境模式
```

### 3. 运行示例

```bash
# 开发模式运行
npm run dev

# 或构建后运行
npm run build
npm start
```

## 日志输出

示例程序会将日志同时输出到：

1. **控制台**: 美化格式，便于开发调试
2. **本地文件**: `logs/YYYYMMDD-HH/sls-pino-example.log`
3. **阿里云 SLS**: 结构化存储，便于查询分析

### 本地文件结构

```
logs/
├── current -> 20241213-14          # 当前小时软链接
├── 20241213-14/                    # 按小时分目录
│   ├── README.md                   # 目录说明
│   └── sls-pino-example.log        # 日志文件
└── 20241213-15/                    # 下一小时目录
    └── sls-pino-example.log
```

## 代码示例

### 基础使用

```typescript
import { createLogger } from '@yai-nexus/pino-support';

// 创建 logger（自动配置控制台 + 文件输出）
const logger = createLogger({
  serviceName: 'my-service',
  level: 'info',
  console: { enabled: true, pretty: true },
  file: { enabled: true, strategy: 'hourly' }
});

// 基础日志
logger.info('应用启动');
logger.warn('这是一个警告', { userId: '123' });
```

### SLS 集成

```typescript
import { SlsTransport } from '@yai-nexus/pino-support/sls';

// 创建 SLS transport
const slsTransport = new SlsTransport({
  endpoint: 'cn-hangzhou.log.aliyuncs.com',
  accessKeyId: process.env.SLS_AK_ID!,
  accessKeySecret: process.env.SLS_AK_KEY!,
  project: 'my-project',
  logstore: 'my-logstore',
  level: 'info'
});

await slsTransport.start();

// 创建带 SLS 的 logger
const logger = createLogger({
  serviceName: 'my-service',
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
```

### 上下文日志

```typescript
// 创建带上下文的子 logger
const requestLogger = logger.child({
  requestId: 'req_123',
  userId: 'user_456',
  traceId: 'trace_789'
});

requestLogger.info('处理用户请求');
requestLogger.error('请求处理失败', { 
  error: 'Database connection timeout',
  duration: 5000 
});
```

## 与 Python 版本对比

| 功能 | Python (loguru-support) | Node.js (pino-support) |
|------|-------------------------|-------------------------|
| **配置接口** | `setup_logging()` | `createLogger()` |
| **目录策略** | `HourlyDirectoryStrategy` | `hourly` strategy |
| **SLS 集成** | `AliyunSlsSink` | `SlsTransport` |
| **环境检测** | ❌ | ✅ (同构) |
| **配置结构** | Dict | TypeScript interface |

两个版本提供语义一致的 API，可以无缝切换。

## 故障排除

### 1. SLS 连接失败

```bash
# 检查网络连接
curl -I https://cn-hangzhou.log.aliyuncs.com

# 检查环境变量
echo $SLS_ENDPOINT $SLS_AK_ID $SLS_PROJECT $SLS_LOGSTORE
```

### 2. 文件日志权限问题

确保程序有权限在当前目录下创建 `logs/` 文件夹。

### 3. 依赖版本问题

确保 Node.js 版本 >= 18，使用最新版本的 `@yai-nexus/pino-support`。

## 相关资源

- [阿里云 SLS 文档](https://help.aliyun.com/product/28958.html)
- [Pino 日志库](https://github.com/pinojs/pino)
- [YAI Nexus AgentKit](../../README.md)

## 许可证

MIT License