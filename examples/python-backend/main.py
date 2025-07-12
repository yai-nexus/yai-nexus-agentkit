#!/usr/bin/env python3
"""
Simple Python backend example for yai-nexus-fekit SDK
This is a minimal echo server that demonstrates the ag-ui-protocol integration
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
import time
import asyncio
from typing import Dict, Any, AsyncGenerator, List, Optional
import uuid
from pydantic import BaseModel

# 核心依赖 - 从 ag-ui 导入标准事件和请求模型
from ag_ui.core import RunAgentInput
from ag_ui.core.events import (
    EventType,
    RunStartedEvent,
    TextMessageChunkEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    RunFinishedEvent,
)

# 日志系统 - 使用新的统一日志系统
from yai_nexus_agentkit.core.logging import logger, get_logger
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 为当前模块创建专用 logger
module_logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 日志中间件，为每个请求添加追踪和性能监控
    """
    
    async def dispatch(self, request: Request, call_next):
        # 生成请求 ID 和追踪信息
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # 生成追踪 ID（在端点内部会处理具体的 trace_id 提取）
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        
        # 创建请求级别的 logger
        req_logger = module_logger.with_trace_id(trace_id).bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None
        )
        
        # 将 logger 和追踪信息存储到请求状态中
        request.state.logger = req_logger
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # 记录请求开始
        req_logger.info("Request started",
                       client_ip=request.client.host if request.client else None,
                       user_agent=request.headers.get("user-agent"))
        
        try:
            # 处理请求
            response = await call_next(request)
            duration = time.time() - start_time
            
            # 记录请求完成
            req_logger.info("Request completed",
                           status_code=response.status_code,
                           duration_ms=round(duration * 1000, 2))
            
            # 添加追踪头到响应
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录请求失败
            req_logger.exception("Request failed",
                                error=str(e),
                                error_type=type(e).__name__,
                                duration_ms=round(duration * 1000, 2))
            raise


app = FastAPI(
    title="YAI Nexus FeKit Python Backend",
    description="Example backend for demonstrating yai-nexus-agentkit integration",
    version="0.1.0"
)

# 添加日志中间件（在 CORS 之前）
app.add_middleware(LoggingMiddleware)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- This is no longer needed, we use RunAgentInput from the library ---
# class ChatMessage(BaseModel):
#     """Represents a single message in the chat history."""
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     """
#     Represents the request body sent by the fekit client.
#     Based on common AG-UI patterns.
#     """
#     messages: List[ChatMessage]
#     threadId: Optional[str] = None
#     runId: Optional[str] = None
#     properties: Optional[Dict[str, Any]] = None


# --- This is no longer needed, we use RunAgentInput from the library ---
# class MessageRequest(BaseModel):
#     content: str
#     metadata: Dict[str, Any] = {}

# class AgUiEvent(BaseModel):
#     type: str
#     data: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "message": "YAI Nexus FeKit Python Backend",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

async def generate_streaming_response(content: str, run_id: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response that simulates an AI agent
    responding with ag-ui-protocol events, using official event models.
    """
    # 创建带上下文的 logger
    ctx_logger = module_logger.with_trace_id(thread_id).bind(
        run_id=run_id,
        thread_id=thread_id
    )
    
    ctx_logger.info("Generating streaming response", content=content)
    
    # Start event
    start_event = RunStartedEvent(
        type=EventType.RUN_STARTED,
        run_id=run_id,
        thread_id=thread_id
    )
    yield f"data: {start_event.model_dump_json()}\n\n"
    await asyncio.sleep(0.5)
    
    # Simulate streaming text response
    response_text = f"Echo: {content}\n\nThis is a demonstration using ag_ui.core.events. Your message was received and processed."
    words = response_text.split()
    for i, word in enumerate(words):
        chunk_event = TextMessageChunkEvent(
            type=EventType.TEXT_MESSAGE_CHUNK,
            delta=word + " "
        )
        yield f"data: {chunk_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)
    
    # Tool call demonstration
    if "tool" in content.lower() or "function" in content.lower():
        tool_call_id = f"tool_call_{uuid.uuid4().hex}"
        # ... (rest of tool call logic from before)
        tool_call_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            tool_call_name="echo_tool"
        )
        yield f"data: {tool_call_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)

        args_event = ToolCallArgsEvent(
            type=EventType.TOOL_CALL_ARGS,
            tool_call_id=tool_call_id,
            delta=json.dumps({"input": content})
        )
        yield f"data: {args_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.3)
        
        end_event = ToolCallEndEvent(
             type=EventType.TOOL_CALL_END,
             tool_call_id=tool_call_id
        )
        yield f"data: {end_event.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)

        result_event = ToolCallResultEvent(
            type=EventType.TOOL_CALL_RESULT,
            tool_call_id=tool_call_id,
            message_id=tool_call_id, # Simplified for example
            content=f"Tool executed successfully with input: {content}"
        )
        yield f"data: {result_event.model_dump_json()}\n\n"

    # End event
    end_event = RunFinishedEvent(
        type=EventType.RUN_FINISHED,
        run_id=run_id,
        thread_id=thread_id,
    )
    yield f"data: {end_event.model_dump_json()}\n\n"
    ctx_logger.info("Finished generating streaming response")


@app.post("/invoke")
async def invoke_agent(request_data: RunAgentInput, request: Request):
    """
    Main endpoint that receives AG-UI standard RunAgentInput
    and returns streaming ag-ui-protocol responses.
    """
    # 使用中间件提供的 logger，并添加端点特定的上下文
    base_logger = request.state.logger
    
    # 提取业务级别的 trace_id（优先使用业务数据中的 ID）
    business_trace_id = request_data.thread_id or request_data.run_id
    
    # 创建端点级别的 logger
    req_logger = base_logger.bind(
        run_id=request_data.run_id,
        thread_id=request_data.thread_id,
        business_trace_id=business_trace_id,
        endpoint="/invoke"
    )
    
    try:
        req_logger.info("Received agent invoke request", 
                       message_count=len(request_data.messages))
        req_logger.debug("Full request details", request=request_data.model_dump())

        if not request_data.messages:
            raise HTTPException(status_code=400, detail="Request body must contain 'messages' array.")

        last_message = request_data.messages[-1]
        content = last_message.content.strip()

        if not content:
            raise HTTPException(status_code=400, detail="The last message must have non-empty 'content'.")

        req_logger.info("Processing message content", content=content)
        
        # Use IDs from the request, or generate new ones
        run_id = request_data.run_id or f"run_{uuid.uuid4().hex}"
        thread_id = request_data.thread_id or f"thread_{uuid.uuid4().hex}"

        return StreamingResponse(
            generate_streaming_response(content, run_id=run_id, thread_id=thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        req_logger.exception("Error processing request", 
                           error=str(e),
                           error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))



# --- The old /test endpoint, kept for simple checks ---
class MessageRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

@app.post("/test")
async def test_endpoint(request: MessageRequest):
    """
    Simple test endpoint that returns a non-streaming response
    """
    return {
        "echo": request.content,
        "metadata": request.metadata,
        "timestamp": time.time(),
        "message": "This is a test response from the Python backend"
    }

if __name__ == "__main__":
    import uvicorn
    
    # 服务器配置
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    module_logger.info("Starting YAI Nexus FeKit Python Backend...",
                      host=host, port=port)
    module_logger.info("Backend will be available at: http://{}:{}".format(host, port))
    module_logger.info("API documentation at: http://{}:{}/docs".format(host, port))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )