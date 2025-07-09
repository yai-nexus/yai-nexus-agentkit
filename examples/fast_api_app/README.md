# FastAPI 交互适配器示例

本示例展示了如何使用 `yai-nexus-agentkit` 的交互适配器实现渐进式的流式响应 API。

## 功能层次

### 1. 简单模式 (已有)
- **路径**: `/chat/simple`
- **功能**: 直接 LLM 调用，无流式处理
- **适用场景**: 基础聊天功能，简单集成
- **依赖**: 仅需核心 LLM 功能

### 2. 中级模式 (新增)
- **路径**: `/chat/stream-basic`
- **功能**: 基础 SSE 流式响应
- **适用场景**: 需要流式体验但不需要复杂协议
- **依赖**: `sse-starlette`

### 3. 高级模式 (新增)
- **路径**: `/chat/stream-advanced`
- **功能**: 完整的 AG-UI 协议支持
- **适用场景**: 标准化事件模型和复杂交互
- **依赖**: `ag-ui-protocol` + `sse-starlette`

## 安装和运行

### 1. 安装依赖

```bash
# 基础功能
pip install -e ".[fastapi]"

# 如果要使用完整功能，确保安装了 ag-ui-protocol
pip install ag-ui-protocol
```

### 2. 配置环境变量

创建 `.env` 文件：
```bash
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
MODEL_TO_USE=gpt-4o-mini  # 可选
```

### 3. 运行服务器

```bash
python -m examples.fast_api_app.main
```

服务器将在 `http://localhost:8000` 启动。

### 4. 测试 API

```bash
# 运行演示客户端
python -m examples.fast_api_app.demo_client

# 或者手动测试
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!"}'
```

## API 文档

### 简单模式

```bash
POST /chat/simple
Content-Type: application/json

{
  "message": "Hello, world!",
  "user_id": "optional-user-id"
}
```

响应：
```json
{
  "response": "Hello! How can I help you today?"
}
```

### 中级模式 (SSE)

```bash
POST /chat/stream-basic
Content-Type: application/json

{
  "message": "Tell me a story",
  "user_id": "optional-user-id"
}
```

SSE 响应格式：
```
event: start
data: {"event": "start", "data": {"status": "processing", "message": "正在处理..."}}

event: content
data: {"event": "content", "data": {"content": "Once upon a time", "delta": true}}

event: content
data: {"event": "content", "data": {"content": "...", "delta": true}}

event: complete
data: {"event": "complete", "data": {"status": "done", "full_response": "..."}}
```

### 高级模式 (AG-UI)

```bash
POST /chat/stream-advanced
Content-Type: application/json

{
  "id": "task-123",
  "query": "Explain quantum computing"
}
```

AG-UI 事件格式：
```
data: {"status": "running"}
data: {"content": "Quantum computing is..."}
data: {"content": " a revolutionary approach..."}
data: {"status": "done"}
```

## 能力检查

```bash
GET /chat/capabilities
```

返回当前 API 支持的功能和依赖状态。

## 架构说明

### 适配器层次结构

```
src/yai_nexus_agentkit/adapter/
├── __init__.py           # 模块导出
├── sse_basic.py          # 基础 SSE 适配器
└── sse_advanced.py       # 高级 AG-UI 适配器
```

### 设计原则

1. **渐进式增强**: 从简单到复杂，用户可以根据需求选择合适的层次
2. **优雅降级**: 缺少依赖时提供清晰的错误信息
3. **标准兼容**: 高级模式遵循 AG-UI 协议标准
4. **易于扩展**: 清晰的接口设计支持自定义扩展

## 故障排除

### 常见问题

1. **SSE 不工作**: 确保安装了 `sse-starlette`
2. **AG-UI 协议错误**: 确保安装了 `ag-ui-protocol`
3. **LLM 调用失败**: 检查 API 密钥配置
4. **依赖冲突**: 使用虚拟环境隔离依赖

### 调试技巧

1. 使用 `/chat/capabilities` 检查功能支持
2. 查看服务器日志了解详细错误
3. 使用演示客户端测试各个模式
4. 检查环境变量配置

## 扩展指南

### 添加新的事件类型

在 `sse_advanced.py` 中的 `event_stream_adapter` 方法中添加新的事件处理：

```python
elif kind == "on_custom_event":
    # 处理自定义事件
    yield json.dumps(CustomEvent(...).model_dump())
```

### 集成真实的 langgraph Agent

替换 `LanggraphAgentMock` 为真实的 langgraph Agent：

```python
from your_langgraph_module import YourAgent

agent = YourAgent()
adapter = AGUIAdapter(agent)
```

### 自定义 SSE 事件

继承 `BasicSSEAdapter` 并重写 `stream_response` 方法：

```python
class CustomSSEAdapter(BasicSSEAdapter):
    async def stream_response(self, message: str, **kwargs):
        # 自定义实现
        pass
```