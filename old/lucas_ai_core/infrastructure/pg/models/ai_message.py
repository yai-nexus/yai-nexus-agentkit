#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Nero Claudius
@date: 2025/4/24
@version: 0.0.1
"""

from typing import Dict, Any

from tortoise import Model, fields

from ..extra.extra_fields import BigIntStrField


class AiMessage(Model):
    id = BigIntStrField(pk=True, description="id")
    conversation_id = BigIntStrField(description="会话id")
    role = fields.CharField(max_length=128, description="角色")
    content = fields.JSONField(description="ai消息", default={})
    created_at = fields.DatetimeField(
        auto_now_add=True, description="创建时间", null=True
    )
    updated_at = fields.DatetimeField(description="更新时间", null=True, auto_now=True)
    deleted_at = fields.DatetimeField(description="删除时间", default=None, null=True)

    class Meta:
        table = "ai_message"
        table_description = "AI会话消息"

    def __str__(self):
        return (
            f"AiMessage(id={self.id}, conversation_id={self.conversation_id}, "
            f"role={self.role}, content={self.content},created_at={self.created_at})"
        )

    def __dict__(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
