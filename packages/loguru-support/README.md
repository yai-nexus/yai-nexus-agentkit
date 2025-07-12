# YAI Loguru Support

A collection of Loguru sinks for integrating with third-party cloud logging services.

## 功能特性

- 🚀 **高性能异步日志传输**：基于官方 SDK 的批量、异步日志发送
- 🔧 **即插即用**：简单的 API，与现有 loguru 配置无缝集成
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

### 2. 阿里云 SLS 集成

```python
import os
from loguru import logger
from yai_loguru_support.sls import AliyunSlsSink

# 创建 SLS sink
sls_sink = AliyunSlsSink(
    endpoint=os.environ['SLS_ENDPOINT'],
    access_key_id=os.environ['SLS_AK_ID'],
    access_key=os.environ['SLS_AK_KEY'],
    project=os.environ['SLS_PROJECT'],
    logstore=os.environ['SLS_LOGSTORE']
)

# 添加到 loguru
logger.add(sls_sink, serialize=True, level="INFO")

# 正常使用 loguru
logger.info("Hello from Aliyun SLS!", user_id="123", action="login")

# 优雅停机
import atexit
atexit.register(sls_sink.stop)
```

### 3. 在 FastAPI 中使用

```python
from fastapi import FastAPI
from yai_loguru_support.sls import AliyunSlsSink
from yai_nexus_agentkit.core.logging import logger

app = FastAPI()

# 生产环境自动启用 SLS
if os.getenv("ENV") == "production":
    sls_sink = AliyunSlsSink(
        endpoint=os.environ['SLS_ENDPOINT'],
        access_key_id=os.environ['SLS_AK_ID'],
        access_key=os.environ['SLS_AK_KEY'],
        project=os.environ['SLS_PROJECT'],
        logstore=os.environ['SLS_LOGSTORE']
    )
    logger.add(sls_sink, serialize=True, level="INFO")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        sls_sink.stop()

@app.get("/")
async def root():
    logger.info("API called", endpoint="/", method="GET")
    return {"message": "Hello World"}
```

## 环境变量

```bash
# 阿里云 SLS 配置
SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
SLS_AK_ID=your_access_key_id
SLS_AK_KEY=your_access_key_secret
SLS_PROJECT=your_log_project
SLS_LOGSTORE=your_log_store
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