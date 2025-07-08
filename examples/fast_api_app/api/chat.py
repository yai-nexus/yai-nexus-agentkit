# -*- coding: utf-8 -*-
"""API 路由模块，定义了聊天相关的端点。"""
from fastapi import APIRouter
from typing import TYPE_CHECKING
from pydantic import BaseModel

# 使用 TYPE_CHECKING 来避免循环导入，这在大型应用中很常见。
if TYPE_CHECKING:
    from ..main import AppContainer

class ChatRequest(BaseModel):
    """聊天请求的模型，用于从请求体中接收 prompt。"""
    prompt: str


def create_router(container: "AppContainer") -> APIRouter:
    """
    创建并返回一个包含聊天端点的 FastAPI 路由。

    Args:
        container: 应用的依赖注入容器实例。

    Returns:
        一个配置好的 APIRouter 实例。
    """
    router = APIRouter(
        prefix="/chat",
        tags=["Chat"],
    )

    # 从容器中获取服务实例
    chat_service = container.chat_service

    @router.post("/")
    async def handle_chat(request: ChatRequest):
        """
        处理聊天请求，返回 AI 的回复。
        """
        reply = await chat_service.get_reply(request.prompt)
        return {"reply": reply}

    return router 