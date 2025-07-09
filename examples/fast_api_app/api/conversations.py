# -*- coding: utf-8 -*-
"""对话管理 API 路由。"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import uuid

from ..main import container
from ..core.services import ConversationService
from yai_nexus_agentkit.persistence.models import AgentConversation

router = APIRouter(prefix="/conversations", tags=["conversations"])


# --- 请求和响应模型 ---
class ConversationCreateRequest(BaseModel):
    """创建对话请求模型"""
    title: Optional[str] = None
    metadata: Optional[dict] = None


class ConversationUpdateRequest(BaseModel):
    """更新对话请求模型"""
    title: Optional[str] = None
    metadata: Optional[dict] = None


class ConversationResponse(BaseModel):
    """对话响应模型"""
    id: str
    title: Optional[str]
    metadata_: Optional[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# --- 依赖注入 ---
def get_conversation_service() -> ConversationService:
    """获取对话服务实例"""
    return container.conversation_service


# --- API 路由 ---
@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = 100,
    offset: int = 0,
    service: ConversationService = Depends(get_conversation_service)
):
    """列出对话"""
    conversations = await service.list_conversations(limit=limit, offset=offset)
    return [ConversationResponse.from_orm(conv) for conv in conversations]


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    """创建对话"""
    conversation = await service.create_conversation(
        title=request.title,
        metadata=request.metadata
    )
    return ConversationResponse.from_orm(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """获取对话"""
    conversation = await service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ConversationResponse.from_orm(conversation)


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    """更新对话"""
    conversation = await service.update_conversation(
        conversation_id,
        title=request.title,
        metadata=request.metadata
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return ConversationResponse.from_orm(conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """删除对话"""
    success = await service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "对话已删除"}


@router.get("/stats/count")
async def get_conversation_count(
    service: ConversationService = Depends(get_conversation_service)
):
    """获取对话数量统计"""
    count = await service.count_conversations()
    return {"count": count}