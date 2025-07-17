# @yai-nexus/loguru-support

`@yai-nexus/loguru-support` 是一个为 Python 应用设计的、统一且可扩展的日志解决方案。它基于强大的 [Loguru](https://loguru.readthedocs.io/) 库，并在此之上提供了标准化的配置、开箱即用的文件轮转策略以及与云服务的无缝集成。

## 🌟 核心特性

- **一键式配置**: 提供 `setup_dev_logging`, `setup_prod_logging` 等便捷函数，无需手动配置即可拥有开发和生产环境的最佳日志实践。
- **智能文件轮转**: 内置按小时或按天轮转日志文件的策略，自动管理日志目录，并创建 `current` 软链接方便追踪最新日志。
- **云服务集成**: 提供可插拔的云日志服务 Sink，目前已支持阿里云 SLS，并为其他服务（如 DataDog, Sentry）预留了扩展点。
- **生产就绪**: 为云服务 Sink 提供异步批量发送、优雅停机、错误重试等生产级特性，确保日志数据不丢失。
- **原生 Loguru 体验**: 完全兼容 Loguru 的所有 API，您无需改变现有的日志记录习惯。

## 💿 安装

1.  **基础安装**:
    ```bash
    pip install yai-loguru-support
    ```

2.  **安装特定云服务支持**:
    ```bash
    # 安装阿里云 SLS 支持
    pip install "yai-loguru-support[sls]"
    
    # 将来支持 Sentry
    # pip install "yai-loguru-support[sentry]"
    ```
    
3.  **安装所有可选依赖**:
    ```bash
    pip install "yai-loguru-support[all]"
    ```

## 🚀 快速上手

### 推荐：使用便捷函数

这是最简单、最推荐的使用方式。

```python
from yai_loguru_support import setup_dev_logging, setup_prod_logging
from loguru import logger
import os

# 根据环境变量选择配置
# 在开发环境，日志会以美化格式打印到控制台，并按小时写入文件。
# 在生产环境，日志会以 JSON 格式打印，便于机器解析。
if os.getenv("ENV") == "production":
    setup_prod_logging("my-service")
else:
    setup_dev_logging("my-service")

# 然后就可以在任何地方使用标准的 loguru logger 了
logger.info("服务已启动", version="1.0.0")
logger.warning("这是一个警告信息")
```

### 深入：集成阿里云 SLS

当您需要在生产环境中将日志发送到云端时，可以轻松添加云服务 Sink。

```python
import os
from loguru import logger
from yai_loguru_support import setup_prod_logging
from yai_loguru_support.sls import AliyunSlsSink
from yai_loguru_support.utils import create_production_setup

# 1. 像往常一样设置基础日志（文件和控制台）
setup_prod_logging("my-api-service")

# 2. 从环境变量创建并添加 AliyunSlsSink
#    (需要预先设置 SLS_ENDPOINT, SLS_AK_ID 等环境变量)
try:
    sls_sink = AliyunSlsSink.from_env()
    logger.add(sls_sink, serialize=True, level="INFO")
    
    # 3. (关键) 设置优雅停机，确保所有日志都被发送
    create_production_setup([sls_sink])
    
    logger.info("已成功集成阿里云 SLS。")
except Exception as e:
    logger.warning(f"集成阿里云 SLS 失败: {e}")


# 您的应用代码...
logger.info("处理了一个重要请求", user_id="user-123")
```

## 📁 智能日志目录结构

使用文件日志时，`loguru-support` 会自动创建结构化的目录，非常便于管理和查阅。

```
logs/
├── current -> 20241213-14/     # 指向当前小时目录的软链接
├── 20241213-14/               # 按小时创建的目录
│   ├── README.md              # 自动生成的说明文件
│   └── my-service.log         # 您服务的日志文件
└── 20241213-15/
    └── my-service.log
```

## 🧪 运行测试

在 `packages/loguru-support` 目录下运行：
```bash
pytest
```

## 🤝 贡献

我们欢迎任何形式的社区贡献，无论是新的云服务 Sink 实现还是功能改进。