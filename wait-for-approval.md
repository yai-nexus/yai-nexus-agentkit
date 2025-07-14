# SSE 解析问题解决方案

## 问题分析

通过浏览器测试发现，当前的聊天功能无法正常工作，主要问题是：

1. **SSE 格式解析错误**：Python 后端返回的是标准 SSE 格式 `data: {JSON对象}`，但 AG-UI HttpAgent 期望的是纯 JSON 格式
2. **错误信息**：`Unexpected token 'd', "data: {"ty"... is not valid JSON`
3. **根本原因**：AG-UI HttpAgent 内部的 SSE 解析器与我们的 Python 后端 SSE 格式不兼容

## 当前架构流程

```
用户消息 → CopilotKit → YaiNexusServiceAdapter.process() → HttpAgent.run() → Python /agui 端点
                                                                ↓
                                                        SSE: "data: {JSON}"
                                                                ↓
                                                        AG-UI HttpAgent 内部解析器
                                                                ↓
                                                            解析失败 ❌
```

## 新发现：CopilotKit 与 AG-UI 的内置集成

经过研究 CopilotKit 官方文档和 AG-UI 协议，我发现：

1. **CopilotKit 和 AG-UI 确实是同一家公司的产品**
2. **AG-UI HttpAgent 应该内置支持 SSE 解析**
3. **问题可能在于我们的 SSE 格式与 AG-UI 期望的格式不完全匹配**

## 解决方案：修复 Python 后端的 SSE 格式

### 方案概述

根据 CopilotKit 官方文档和 AG-UI 协议规范，问题在于我们的 Python 后端 SSE 格式与 AG-UI HttpAgent 期望的格式不匹配。

### 问题根源

查看 AG-UI 官方文档，正确的 SSE 格式应该是：

1. **AG-UI HttpAgent 期望直接接收 AG-UI JSON 事件**，而不是包装在 SSE `data:` 字段中
2. **我们的 Python 后端在 `/agui` 端点中添加了额外的 SSE 包装**

### 解决方案：修改 Python 后端

#### 方案一：创建专门的非 SSE 端点

为 AG-UI HttpAgent 创建一个返回纯 JSON 流的端点：

```python
# examples/python-backend/main.py

@app.post("/agui-json")
async def agui_json_agent(request_data: RunAgentInput, request: Request):
    """
    为 AG-UI HttpAgent 提供的纯 JSON 流式端点
    直接返回 AG-UI JSON 对象，不包装在 SSE 中
    """
    req_logger = request.state.logger.bind(
        run_id=request_data.run_id, thread_id=request_data.thread_id, endpoint="/agui-json"
    )

    try:
        # ... 验证逻辑 ...

        # 创建 Task 对象
        task = Task(
            id=request_data.run_id or f"run_{uuid.uuid4().hex}",
            query=last_message.content,
            thread_id=request_data.thread_id or f"thread_{uuid.uuid4().hex}",
        )

        # 直接返回 AG-UI JSON 流，不包装在 SSE 中
        async def agui_json_stream():
            try:
                async for event_json in agui_adapter.event_stream_adapter(task):
                    # 直接 yield JSON 字符串，不添加 SSE 格式
                    yield event_json + '\n'

            except Exception as e:
                req_logger.error("Error in AG-UI JSON streaming", error=str(e))
                # 发送错误事件
                error_event = {
                    "type": "RUN_ERROR",
                    "message": str(e),
                    "timestamp": None,
                    "raw_event": None,
                }
                yield json.dumps(error_event) + '\n'

        # 返回纯文本流，每行一个 JSON 对象
        return StreamingResponse(
            agui_json_stream(),
            media_type="application/x-ndjson"  # Newline Delimited JSON
        )

    except Exception as e:
        # ... 错误处理 ...
```

#### 方案二：修改前端使用新端点

修改前端 `YaiNexusServiceAdapter` 使用新的 JSON 端点：

```typescript
// packages/fekit/src/handler.ts

class YaiNexusServiceAdapter implements CopilotServiceAdapter {
  constructor(backendUrl: string, options: CreateYaiNexusHandlerOptions) {
    // 使用 /agui-json 端点，返回纯 JSON 流
    const aguiUrl = backendUrl.endsWith("/")
      ? `${backendUrl}agui-json`
      : `${backendUrl}/agui-json`;

    this.httpAgent = new HttpAgent({
      url: aguiUrl,
      description: "YAI Nexus Agent for AG-UI protocol",
    });

    // ... 其余代码保持不变 ...
  }
}
```

#### 方案三：使用 AG-UI 官方的 EventEncoder

参考 AG-UI 官方文档，使用正确的事件编码器：

```python
# examples/python-backend/main.py
from ag_ui.encoder import EventEncoder

@app.post("/agui")
async def agui_agent(request_data: RunAgentInput, request: Request):
    """
    使用 AG-UI 官方 EventEncoder 的正确实现
    """
    # 获取 accept header
    accept_header = request.headers.get("accept")

    # 创建 AG-UI 官方的事件编码器
    encoder = EventEncoder(accept=accept_header)

    async def event_generator():
        try:
            async for event_json in agui_adapter.event_stream_adapter(task):
                # 解析 JSON 字符串为对象
                event_obj = json.loads(event_json)

                # 使用官方编码器编码事件
                yield encoder.encode(event_obj)

        except Exception as e:
            # 使用编码器编码错误事件
            error_event = {
                "type": "RUN_ERROR",
                "message": str(e),
            }
            yield encoder.encode(error_event)

    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )
```

### 推荐方案：方案三（使用 AG-UI 官方 EventEncoder）

**理由：**
1. **符合官方规范**：使用 AG-UI 官方提供的 EventEncoder
2. **最小改动**：只需要修改 Python 后端的编码方式
3. **向前兼容**：确保与未来的 AG-UI 更新兼容
4. **类型安全**：官方编码器处理所有格式细节

### 实施步骤

1. **安装 AG-UI Python SDK**（如果还没有）：
   ```bash
   cd examples/python-backend
   poetry add ag-ui
   ```

2. **修改 Python 后端**：
   - 导入 `EventEncoder`
   - 修改 `/agui` 端点使用官方编码器
   - 测试编码器的 `accept` header 处理

3. **验证集成**：
   - 测试前端聊天功能
   - 检查浏览器控制台是否还有解析错误
   - 验证 AG-UI 事件流是否正常

### 优势

1. **官方支持**：使用 CopilotKit/AG-UI 官方工具，确保兼容性
2. **最小风险**：只修改后端编码方式，不改变架构
3. **标准化**：符合 AG-UI 协议规范
4. **可维护性**：使用官方工具，减少自定义代码

### 风险评估

- **极低风险**：使用官方工具，只是修改编码方式
- **快速回滚**：如果有问题，可以立即回到当前实现
- **测试简单**：只需要验证聊天功能是否正常

## 请求批准

推荐实施**方案三**，使用 AG-UI 官方的 EventEncoder 来解决 SSE 格式兼容性问题。这是最符合官方规范且风险最低的解决方案。
