# -*- coding: utf-8 -*-
"""对话管理 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from ..app import container
from ..core.services import ConversationService


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    metadata_: Optional[dict] = Field(None, alias="metadata")

    class Config:
        orm_mode = True
        from_attributes = True


router = APIRouter()


# --- 请求和响应模型 ---
class ConversationCreateRequest(BaseModel):
    """创建对话请求模型"""

    title: Optional[str] = None
    metadata: Optional[dict] = None


class ConversationUpdateRequest(BaseModel):
    """更新对话请求模型"""

    title: Optional[str] = None
    metadata: Optional[dict] = None


# --- 依赖注入 ---
def get_conversation_service() -> ConversationService:
    """获取对话服务实例"""
    return container.conversation_service()


# --- API 路由 ---
@router.post("/", response_model=ConversationResponse)
async def create_conversation_endpoint(
    title: str = None,
    metadata: dict = None,
    service: ConversationService = Depends(get_conversation_service),
):
    """创建对话"""
    conv = await service.create_conversation(title=title, metadata=metadata)
    return ConversationResponse.from_orm(conv)


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations_endpoint(
    limit: int = 100,
    offset: int = 0,
    service: ConversationService = Depends(get_conversation_service),
):
    """列出对话"""
    convs = await service.list_conversations(limit=limit, offset=offset)
    return [ConversationResponse.from_orm(c) for c in convs]


@router.get("/{convo_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(
    convo_id: str, service: ConversationService = Depends(get_conversation_service)
):
    """获取对话"""
    conversation = await service.get_conversation(convo_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.from_orm(conversation)


@router.put("/{convo_id}", response_model=ConversationResponse)
async def update_conversation_endpoint(
    convo_id: str,
    title: str = None,
    metadata: dict = None,
    service: ConversationService = Depends(get_conversation_service),
):
    """更新对话"""
    conversation = await service.update_conversation(
        convo_id, title=title, metadata=metadata
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.from_orm(conversation)


@router.delete("/{convo_id}", status_code=204)
async def delete_conversation_endpoint(
    convo_id: str, service: ConversationService = Depends(get_conversation_service)
):
    """删除对话"""
    success = await service.delete_conversation(convo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return


@router.get("/stats/count")
async def get_conversation_count(
    service: ConversationService = Depends(get_conversation_service),
):
    """获取对话数量统计"""
    count = await service.count_conversations()
    return {"count": count}
