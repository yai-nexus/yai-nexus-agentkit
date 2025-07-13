# SLS 日志集成示例

这是一个简化的示例，演示如何用最少的代码将 Loguru 日志发送到阿里云 SLS (Simple Log Service)。

## 功能特点

- **极简配置** - 从环境变量自动配置，无需手写配置文件
- **轻量依赖** - 只依赖 `yai-loguru-support[sls]`，无需 yai-nexus-agentkit
- **生产就绪** - 包含优雅停机机制，确保日志完整发送
- **标准 API** - 使用原生 Loguru API，学习成本低

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
export SLS_ENDPOINT=cn-hangzhou.log.aliyuncs.com
export SLS_AK_ID=your_access_key_id
export SLS_AK_KEY=your_access_key_secret
export SLS_PROJECT=your_project
export SLS_LOGSTORE=your_logstore

# 可选配置
export SLS_TOPIC=python-app        # 默认: python-app
export SLS_SOURCE=your-app-name    # 默认: yai-loguru-support
```

### 3. 运行示例

```bash
python main.py
```

## 环境变量说明

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `SLS_ENDPOINT` | ✅ | SLS 服务端点 | `cn-hangzhou.log.aliyuncs.com` |
| `SLS_AK_ID` | ✅ | 阿里云 Access Key ID | `LTAI5t...` |
| `SLS_AK_KEY` | ✅ | 阿里云 Access Key Secret | `xxx...` |
| `SLS_PROJECT` | ✅ | SLS 项目名称 | `my-log-project` |
| `SLS_LOGSTORE` | ✅ | SLS 日志库名称 | `app-logs` |
| `SLS_TOPIC` | ❌ | 日志主题 | `python-app` |
| `SLS_SOURCE` | ❌ | 日志来源 | `my-service` |

## 代码示例

```python
import os
import asyncio
from loguru import logger
from yai_loguru_support.sls import AliyunSlsSink
from yai_loguru_support.utils import create_production_setup

async def main():
    # 1. 从环境变量创建 SLS Sink
    sls_sink = AliyunSlsSink.from_env()
    
    # 2. 添加到 loguru
    logger.add(sls_sink, serialize=True, level="INFO")
    
    # 3. 设置优雅停机
    create_production_setup([sls_sink])
    
    # 4. 发送日志
    logger.info("Hello SLS!", user_id="123")
    
    # 5. 等待发送完成
    await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
```

## 获取阿里云 SLS 配置

1. **登录阿里云控制台** → 日志服务 SLS
2. **创建项目和日志库**（如果还没有）
3. **获取 Endpoint**：在项目概览页面可以看到
4. **获取 Access Key**：阿里云控制台 → AccessKey 管理

## 对比原版示例

| 特性 | 原版 sls_example.py | 简化版 main.py |
|------|-------------------|----------------|
| 代码行数 | 210 行 | 80 行 |
| 依赖数量 | yai-nexus-agentkit + yai-loguru-support | 仅 yai-loguru-support |
| 功能范围 | 监控+告警+日志 | 仅日志集成 |
| 学习成本 | 高 | 低 |
| 维护成本 | 高 | 低 |

## 注意事项

- SLS 使用批量发送优化性能，建议在程序结束前等待几秒确保日志发送完成
- 生产环境建议设置合适的日志级别（INFO 或 WARNING 以上）
- 确保网络能访问阿里云 SLS 服务
- Access Key 请妥善保管，不要提交到代码仓库

## 故障排除

**Q: 提示缺少环境变量？**  
A: 请检查是否设置了所有必需的 `SLS_*` 环境变量

**Q: 连接超时？**  
A: 检查网络连接和 SLS_ENDPOINT 配置是否正确

**Q: 认证失败？**  
A: 确认 Access Key ID 和 Secret 是否正确，且具有 SLS 写入权限

**Q: 找不到项目或日志库？**  
A: 请先在阿里云控制台创建对应的项目和日志库