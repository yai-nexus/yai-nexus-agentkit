# -*- coding: utf-8 -*-
"""API 路由模块，演示如何集成 AG-UI。"""

from functools import partial
from typing import AsyncGenerator

from ag_ui import AgentUI, run_in_thread
from ag_ui.core.events import Error, Message, Node, State, Task, Text
from fastapi import APIRouter
from pydantic import BaseModel

from yai_nexus_agentkit.llm import LLMConfig, LLMProvider, llm_factory

# --- 1. 配置 LLM Factory ---
# 在应用启动时，注册需要使用的模型。
# 这里的 "default_model" 是我们为这个配置起的名字，方便后续调用。
llm_factory.register_config(
    "default_model", LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o")
)


# --- 2. 实现 AG-UI Agent 回调函数 ---
async def my_agent_callback(task: Task) -> AsyncGenerator[Node, None]:
    """
    一个符合 AG-UI 规范的 Agent 回调函数。
    它接收一个任务对象，并异步地产生一系列 UI 事件节点。
    """
    try:
        # 事件：告诉前端，任务已开始
        yield State(status="running")
        # 事件：发送一个静态文本，表明 Agent 正在做什么
        yield Text("正在思考，请稍候...")

        # 从全局工厂获取预先配置好的 LLM 客户端
        # 注意：这里使用的是我们之前注册时使用的 "default_model" ID
        llm_client = llm_factory.get_llm_client("default_model")

        # 使用模型的流式接口获取内容
        content_stream = llm_client.astream(task.query)

        full_response = ""
        # 迭代内容流，并将其转换为 AG-UI 事件
        async for chunk in content_stream:
            content_part = chunk.content
            if content_part:
                full_response += content_part
                # 事件：发送增量的文本内容，实现“打字机”效果
                yield Text(content=content_part)

        # 事件：发送完整的最终消息
        yield Message(id=task.id, role="assistant", content=full_response)
        # 事件：告诉前端，任务已成功完成
        yield State(status="done")

    except Exception as e:
        # 事件：如果发生任何错误，发送一个错误通知
        yield Error(message=str(e), code="INTERNAL_SERVER_ERROR")
        # 事件：告诉前端，任务因错误而终止
        yield State(status="error")


# --- 3. 设置并挂载 AG-UI 路由 ---
router = APIRouter()

# 创建 AgentUI 实例，它会处理所有与前端的 SSE 通信。
# agent_id 是前端用来识别和连接到这个 Agent 的标识符。
agent_ui = AgentUI(agent_id="my-agent", agent_fn=my_agent_callback)

# 将 AgentUI 生成的 FastAPI 路由包含到我们的主路由中
router.include_router(agent_ui.router)

# 在后台线程中运行 AgentUI 的消息循环（如果需要双向通信）
run_in_thread(agent_ui)


# --- 4. (已注释) 原有的 API 端点 ---
#
# from typing import TYPE_CHECKING
# from ..core.services import ChatService, get_chat_service
#
# # 使用 TYPE_CHECKING 来避免循环导入，这在大型应用中很常见。
# if TYPE_CHECKING:
#     from ..core.services import ChatService
#
# class ChatRequest(BaseModel):
#     """聊天请求的数据模型。"""
#
#     user_id: str
#     conversation_id: str | None = None
#     message: str
#
#
# class ChatResponse(BaseModel):
#     """聊天响应的数据模型。"""
#
#     conversation_id: str
#     response: str
#
#
# def get_chat_service() -> ChatService:
#     """
#     依赖注入函数，用于获取 ChatService 的实例。
#     """
#     return ChatService()
#
#
# @router.post("/chat", response_model=ChatResponse)
# async def invoke_llm(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
#     """
#     调用语言模型进行聊天。
#     """
#     response_text = service.process_message(
#         user_id=request.user_id,
#         conversation_id=request.conversation_id,
#         message=request.message,
#     )
#     return ChatResponse(
#         conversation_id=request.conversation_id or "some_new_id",
#         response=response_text
#     )
