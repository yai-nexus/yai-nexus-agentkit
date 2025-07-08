# -*- coding: utf-8 -*-
"""API 路由模块，定义了聊天相关的端点。"""

from fastapi import APIRouter
from typing import TYPE_CHECKING
from pydantic import BaseModel
from fastapi import Depends
from ..core.services import ChatService

# 使用 TYPE_CHECKING 来避免循环导入，这在大型应用中很常见。
if TYPE_CHECKING:
    pass


class ChatRequest(BaseModel):
    """聊天请求的数据模型。"""

    prompt: str


class ChatResponse(BaseModel):
    """聊天响应的数据模型。"""

    response: str


# --- API 路由 ---
router = APIRouter()


def get_chat_service() -> ChatService:
    """依赖注入函数，用于获取 ChatService 实例。"""
    from ..main import container

    return container.chat_service


@router.post("/chat", response_model=ChatResponse)
async def invoke_llm(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """
    调用语言模型进行聊天。
    接收一个包含 prompt 的请求，并返回模型的响应。
    """
    response_text = await service.get_reply(request.prompt)
    return ChatResponse(response=response_text)
