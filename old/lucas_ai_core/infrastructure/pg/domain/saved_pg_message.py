#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Nero Claudius
@date: 2025/6/11
@version: 0.0.1
"""

import uuid
from enum import Enum
from typing import List, Dict, Any

from lucas_common_components.tools.SnowFlake import Snowflake
from pydantic import BaseModel, Field

sf = Snowflake(worker_id=0, datacenter_id=0)


class BlockType(Enum):
    indicator = "indicator"
    typewriter = "typewriter"
    rich_text = "rich_text"
    buttons = "buttons"
    link = "link"
    text = "text"


class Role(Enum):
    ai = "ai"
    user = "user"


class PgMessageContentMessages(BaseModel):
    """
    消息内容中的单条消息
    @see lucas_ai.public.ai_message.content.messages(json field)
    """

    blockId: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="消息id"
    )
    blockType: str | None = Field(
        default=BlockType.typewriter.value, description="消息类型"
    )
    icon: str | None = Field(default=None, description="消息图标")
    params: Dict[str, Any] | None = Field(default=None, description="消息携带参数")
    content: str | None = Field(description="消息内容")
    finish: bool = Field(description="是否结束", default=False)

    @staticmethod
    def of_rich_text(
        content: str,
        icon: str | None = None,
        params: Dict[str, Any] | None = None,
        finish: bool = False,
    ) -> "PgMessageContentMessages":
        return PgMessageContentMessages(
            blockId=str(uuid.uuid4()),
            blockType=BlockType.rich_text.value,
            icon=icon,
            params=params,
            content=content,
            finish=finish,
        )

    @staticmethod
    def of_typewriter(
        content: str,
        icon: str | None = None,
        params: Dict[str, Any] | None = None,
        finish: bool = False,
    ) -> "PgMessageContentMessages":
        return PgMessageContentMessages(
            blockId=str(uuid.uuid4()),
            blockType=BlockType.rich_text.value,
            icon=icon,
            params=params,
            content=content,
            finish=finish,
        )


class PgMessageContent(BaseModel):
    """
    消息内容
    @see lucas_ai.public.ai_message.content(column)
    """

    messages: List[PgMessageContentMessages] = Field(..., description="消息列表")

    @staticmethod
    def of() -> "PgMessageContent":
        return PgMessageContent(messages=[])


class AiMessageBO(BaseModel):
    id: int = Field(description="id")
    conversation_id: str = Field(description="会话id")
    content: PgMessageContent = Field(description="消息内容")
    role: str = Field(description="角色")

    @staticmethod
    def of_ai(conversation_id: str, content: PgMessageContent) -> "AiMessageBO":
        return AiMessageBO(
            id=sf.generate(),
            conversation_id=conversation_id,
            content=content,
            role=Role.ai.value,
        )
