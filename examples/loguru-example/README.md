# `@yai-nexus/loguru-support` 示例：集成云日志服务

本项目提供了一个清晰的示例，演示如何使用 `@yai-nexus/loguru-support` 将您的 Python 应用日志与云日志服务（如此示例中的阿里云 SLS）进行集成。

其核心设计思想是 **配置驱动** 和 **代码极简**，让您可以通过环境变量无缝对接到生产环境的日志基础设施。

## 🌟 核心特性

- **环境驱动配置**：零代码修改，通过环境变量即可完成生产环境的日志配置。
- **生产就绪**：内置优雅停机（Graceful Shutdown）机制，确保在应用退出前所有缓冲的日志都能被成功发送。
- **原生 Loguru API**：无需学习新的日志 API，继续使用您所熟悉的 `loguru` 即可。
- **轻量化设计**：仅依赖于核心的 `loguru-support` 包，无需引入整个 `agentkit`。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install "yai-loguru-support[sls]"
# 该命令会同时安装 loguru-support 和阿里云 SLS 所需的依赖
```

### 2. 配置环境变量

在运行前，请设置以下环境变量以配置阿里云 SLS 连接信息。

| 变量名 | 必填 | 描述 | 示例 |
|:---|:---:|:---|:---|
| `SLS_ENDPOINT` | ✅ | SLS 服务端点 | `cn-hangzhou.log.aliyuncs.com` |
| `SLS_AK_ID` | ✅ | 阿里云 Access Key ID | `LTAI5t...` |
| `SLS_AK_KEY` | ✅ | 阿里云 Access Key Secret | `xxx...` |
| `SLS_PROJECT` | ✅ | SLS 项目名称 | `my-log-project` |
| `SLS_LOGSTORE` | ✅ | SLS 日志库名称 | `app-logs` |
| `SLS_TOPIC` | ❌ | 日志主题 (默认为 `python-app`) | `my-service` |
| `SLS_SOURCE` | ❌ | 日志来源 (默认为 `yai-loguru-support`) | `my-app-instance` |

> **提示**: 您可以在阿里云**日志服务控制台**的项目概览页找到 `Endpoint`，在 **AccessKey 管理**页面创建和获取 Access Key。

### 3. 运行示例

```bash
python main.py
```

运行后，您应该能在阿里云 SLS 控制台的相应日志库中看到 "Hello SLS!" 这条日志。

##  dissected 代码解析

`main.py` 的代码非常简洁，关键步骤如下：

```python
import asyncio
from loguru import logger
from yai_loguru_support.sls import AliyunSlsSink
from yai_loguru_support.utils import create_production_setup

async def main():
    # 1. 从环境变量自动创建 Sink 实例
    # Sink 是 loguru 的术语，代表一个日志输出目标。
    # .from_env() 方法会自动读取 SLS_* 环境变量并完成配置。
    sls_sink = AliyunSlsSink.from_env()
    
    # 2. 将 Sink 添加到 loguru
    # `serialize=True` 会将日志记录转换为 JSON 格式，便于云服务处理。
    logger.add(sls_sink, serialize=True, level="INFO")
    
    # 3. 设置优雅停机钩子
    # 这是关键一步！它能确保在程序退出时，所有在内存中排队的日志
    # 都能被完整发送出去，避免日志丢失。
    create_production_setup([sls_sink])
    
    # 4. 使用标准的 loguru API 发送日志
    logger.info("Hello SLS!", user_id="123", request_id="abc-xyz")
    
    # 5. 等待日志发送
    # 日志是批量异步发送的，这里等待几秒确保发送完成。
    # 在真实应用中，程序会持续运行。
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔌 扩展到其他服务

本示例展示了与阿里云 SLS 的集成，但 `yai-loguru-support` 的设计是可扩展的。您可以参照 `yai_loguru_support/sls` 的实现，轻松创建与其他云日志服务（如 Sentry, DataDog, Grafana Loki 等）集成的 Sink。

核心是实现一个遵循 `loguru` Sink 协议的类，并处理好批量发送和优雅停机。

## 💡 故障排查

- **认证失败?**
  请检查您的 Access Key ID 和 Secret 是否正确，并且该账户拥有对应 SLS Logstore 的写入权限。
- **连接超时?**
  请检查 `SLS_ENDPOINT` 是否正确，以及您的网络环境是否可以访问阿里云服务。
- **找不到项目或日志库?**
  请确保您已在阿里云控制台提前创建了对应的 Project 和 Logstore。