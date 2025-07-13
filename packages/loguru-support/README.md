# YAI Loguru Support

统一的 Python 日志解决方案，提供云服务集成和标准化配置。

## 功能特性

- 🔧 **统一配置接口**：与 pino-support 语义一致的配置体验
- 📁 **智能目录策略**：按小时/天自动分目录，支持软链接和 README
- 🚀 **高性能异步传输**：基于官方 SDK 的批量、异步日志发送
- 🌥️ **多云支持**：支持阿里云 SLS、Datadog、Sentry 等主流云服务
- 🛡️ **生产级可靠性**：优雅停机、错误重试、连接保活
- 📊 **内置监控**：性能指标、错误率统计、健康检查

## 支持的云服务

| 服务 | 状态 | 安装命令 |
|------|------|----------|
| 阿里云 SLS | ✅ 已实现 | `pip install yai-loguru-support[sls]` |
| Datadog | 🚧 开发中 | `pip install yai-loguru-support[datadog]` |
| Sentry | 🚧 开发中 | `pip install yai-loguru-support[sentry]` |

## 快速开始

### 1. 安装

```bash
# 基础安装
pip install yai-loguru-support

# 安装阿里云 SLS 支持
pip install yai-loguru-support[sls]

# 安装所有支持的云服务
pip install yai-loguru-support[all]
```

### 2. 统一日志配置

```python
from yai_loguru_support import setup_logging
from loguru import logger

# 开发环境配置（美化控制台 + 小时级文件）
setup_logging("my-service", {
    "level": "debug",
    "console": {"enabled": True, "pretty": True},
    "file": {"enabled": True, "strategy": "hourly"}
})

# 生产环境配置（JSON控制台 + 小时级文件）
setup_logging("my-service", {
    "level": "info", 
    "console": {"enabled": True, "pretty": False},
    "file": {"enabled": True, "strategy": "hourly"}
})

# 正常使用 loguru
logger.info("应用启动", version="1.0.0")
```

### 3. 便捷配置函数

```python
from yai_loguru_support import setup_dev_logging, setup_prod_logging

# 开发环境 (DEBUG级别，美化输出，小时级文件)
setup_dev_logging("my-service")

# 生产环境 (INFO级别，JSON输出，小时级文件)
setup_prod_logging("my-service")

# 仅控制台 (适用于容器环境)
setup_console_only_logging("my-service")
```

### 4. 阿里云 SLS 集成

```python
from yai_loguru_support import setup_logging
from yai_loguru_support.sls import AliyunSlsSink
from loguru import logger

# 1. 首先设置基础日志配置（控制台 + 文件）
setup_logging("my-service")

# 2. 添加 SLS 云端日志
sls_sink = AliyunSlsSink.from_env()  # 从环境变量自动配置
logger.add(sls_sink, serialize=True, level="INFO")

# 3. 正常使用 loguru（现在会同时输出到控制台、文件和SLS）
logger.info("Hello from Aliyun SLS!", user_id="123", action="login")

# 4. 优雅停机
import atexit
atexit.register(sls_sink.stop)
```

### 5. 在 FastAPI 中使用

```python
from fastapi import FastAPI
from yai_loguru_support import setup_prod_logging
from yai_loguru_support.sls import AliyunSlsSink
from loguru import logger
import os

app = FastAPI()

# 设置统一日志配置
if os.getenv("ENV") == "production":
    setup_prod_logging("my-api")
    
    # 生产环境添加 SLS
    sls_sink = AliyunSlsSink.from_env()
    logger.add(sls_sink, serialize=True, level="INFO")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await sls_sink.stop()
else:
    setup_dev_logging("my-api")

@app.get("/")
async def root():
    logger.info("API called", endpoint="/", method="GET")
    return {"message": "Hello World"}
```

## 日志目录结构

统一配置会在项目根目录下创建结构化的日志目录：

```
logs/
├── current -> 20241213-14          # 当前小时软链接
├── 20241213-14/                    # 按小时分目录
│   ├── README.md                   # 目录说明
│   ├── my-service.log              # 服务日志
│   └── python-backend.log          # 其他服务日志
└── 20241213-15/                    # 下一小时目录
    └── my-service.log
```

## 配置参数说明

### LoggerConfig 配置结构

```python
{
    "level": "info",                    # 日志级别: debug, info, warn, error
    "console": {
        "enabled": True,                # 是否启用控制台输出
        "pretty": True                  # 是否美化输出（开发模式）
    },
    "file": {
        "enabled": True,                # 是否启用文件输出
        "baseDir": "logs",              # 日志根目录
        "strategy": "hourly",           # 目录策略: hourly, daily, simple
        "maxSize": None,                # 文件最大大小（可选）
        "maxFiles": None                # 保留文件数量（可选）
    }
}
```

### 目录策略

- **hourly**: 按小时分目录 `YYYYMMDD-HH/`，适合高频日志
- **daily**: 按天分目录 `YYYYMMDD/`，适合中等频率
- **simple**: 单一文件，适合低频日志

## 环境变量

```bash
# 阿里云 SLS 配置
SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
SLS_AK_ID=your_access_key_id
SLS_AK_KEY=your_access_key_secret
SLS_PROJECT=your_log_project
SLS_LOGSTORE=your_log_store

# 统一日志配置（可选）
LOG_LEVEL=info
LOG_TO_FILE=true
LOG_DIR=logs
```

## 开发

```bash
# 克隆项目
git clone https://github.com/yai-nexus/yai-nexus-agentkit.git
cd yai-nexus-agentkit/packages/loguru-support

# 安装开发依赖
pip install -e ".[dev,all]"

# 运行测试
pytest

# 代码格式化
black .
ruff check .
```

## 许可证

MIT License