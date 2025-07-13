#!/usr/bin/env python3
"""
Python backend example for yai-nexus-fekit, using AGUIAdapter.
"""
import os
import uuid
import time
from typing import TypedDict, Annotated, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# 核心依赖
from ag_ui.core import RunAgentInput
from yai_nexus_agentkit.adapter.sse_advanced import AGUIAdapter, Task
from yai_loguru_support import setup_logging, setup_dev_logging, setup_prod_logging
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志系统已移动到 configure_app_logging 函数中

def check_environment_variables():
    """检查必要的环境变量是否已设置"""
    # 检查多种可用的 API Key
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not any([openai_key, openrouter_key, dashscope_key]):
        logger.error("FATAL: No API key found. Please set one of: OPENAI_API_KEY, OPENROUTER_API_KEY, or DASHSCOPE_API_KEY")
        raise ValueError("At least one LLM API key is required to run the application.")
    
    if openai_key:
        logger.info("OPENAI_API_KEY is configured.")
    elif openrouter_key:
        logger.info("OPENROUTER_API_KEY is configured.")
    elif dashscope_key:
        logger.info("DASHSCOPE_API_KEY is configured.")

# 初始化日志系统和环境检查
# 直接调用我们的日志配置函数
def configure_app_logging():
    """配置应用日志 - 使用 loguru-support 统一日志配置系统"""
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # 生产环境配置
        setup_prod_logging("python-backend", log_level="info")
    else:
        # 开发环境配置
        setup_dev_logging("python-backend")
    
    logger.info("Logging system initialized with loguru-support", 
                environment=environment, 
                service="python-backend")

configure_app_logging()
check_environment_variables()

# --- LangGraph Agent Definition ---

class AgentState(TypedDict):
    """定义 Agent 的状态，包含消息列表"""
    messages: Annotated[List[BaseMessage], add_messages]

# 根据可用的 API Key 创建 LLM 实例
def create_llm():
    """根据环境变量创建合适的 LLM 实例"""
    if os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI ChatGPT")
        return ChatOpenAI(model="gpt-4o")
    elif os.getenv("OPENROUTER_API_KEY"):
        logger.info("Using OpenRouter") 
        return ChatOpenAI(
            model="openai/gpt-4o-mini",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    elif os.getenv("DASHSCOPE_API_KEY"):
        # 使用阿里云通义千问，需要导入对应的库
        try:
            from langchain_community.llms import Tongyi
            logger.info("Using Tongyi (DashScope)")
            return Tongyi(
                model="qwen-turbo",
                dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
            )
        except ImportError:
            logger.warning("langchain_community not available, falling back to OpenRouter")
            # 回退到 OpenRouter
            return ChatOpenAI(
                model="openai/gpt-4o-mini", 
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY") or "fallback"
            )
    else:
        raise ValueError("No suitable LLM configuration found")

llm = create_llm()

# 定义 Agent 节点，该节点将调用 LLM
def llm_agent_node(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """调用 LLM 并返回其响应"""
    logger.info("LLM Agent node is processing the state.")
    return {"messages": [llm.invoke(state["messages"])]}

# 创建 Agent 的图 (Graph)
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", llm_agent_node)
graph_builder.set_entry_point("agent")
graph_builder.set_finish_point("agent")

# 编译图，得到可运行的 Agent
agent = graph_builder.compile()

# --- AGUIAdapter Instantiation ---
# 使用编译好的 Agent 实例化适配器
agui_adapter = AGUIAdapter(agent=agent)


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
        req_logger = logger.bind(
            trace_id=trace_id,
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



@app.post("/invoke")
async def invoke_agent(request_data: RunAgentInput, request: Request):
    """
    接收 AG-UI 标准输入，并使用 AGUIAdapter 返回流式响应。
    """
    req_logger = request.state.logger.bind(
        run_id=request_data.run_id,
        thread_id=request_data.thread_id,
        endpoint="/invoke"
    )

    try:
        req_logger.info("Received agent invoke request",
                       message_count=len(request_data.messages))

        if not request_data.messages:
            raise HTTPException(status_code=400, detail="Request body must contain 'messages' array.")

        last_message = request_data.messages[-1]
        if not last_message.content.strip():
            raise HTTPException(status_code=400, detail="The last message must have non-empty 'content'.")

        # 创建 Adapter 需要的 Task 对象
        task = Task(
            id=request_data.run_id or f"run_{uuid.uuid4().hex}",
            query=last_message.content,
            thread_id=request_data.thread_id or f"thread_{uuid.uuid4().hex}"
        )

        req_logger.info("Forwarding task to AGUIAdapter", task_id=task.id, thread_id=task.thread_id)

        # AGUIAdapter 会自动处理事件流生成和错误捕获
        return EventSourceResponse(
            agui_adapter.event_stream_adapter(task),
            ping=15,
            media_type="text/event-stream"
        )

    except HTTPException as http_exc:
        # 重新抛出 HTTP 异常，让 FastAPI 处理
        raise http_exc
    except Exception as e:
        # 对于其他所有异常，记录并返回一个标准的 500 错误
        req_logger.exception(
            "An unexpected error occurred in /invoke endpoint",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


if __name__ == "__main__":
    import uvicorn
    
    # 服务器配置
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info("Starting YAI Nexus FeKit Python Backend...",
                host=host, port=port)
    logger.info("Backend will be available at: http://{}:{}".format(host, port))
    logger.info("API documentation at: http://{}:{}/docs".format(host, port))
    logger.info("Log files will be stored in hourly directories under logs/")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )