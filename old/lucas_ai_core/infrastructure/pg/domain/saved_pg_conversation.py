#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Nero Claudius
@date: 2025/6/11
@version: 0.0.1
"""

from enum import Enum
from typing import Dict, Any

from pydantic import BaseModel, Field


class IdentityEnum(Enum):
    staff = "staff"
    user = "user"


class AiConversationBO(BaseModel):
    id: str = Field(description="id")
    title: str = Field(description="会话标题/名称")
    context: Dict[str, Any] | None = Field(
        default_factory=lambda: {}, description="附加信息"
    )
    uni_identity_id: str = Field(description="身份id")
    identity_type: str = Field(description="身份类型")
    uni_tenant_id: str | None = Field(description="租户id")
    avatar: str | None = Field(default=None, description="会话头像")
    last_message: str | None = Field(default=None, description="该会话的最后一条消息")
