from datetime import datetime
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q

from ..models.ai_conversation import (
    AIConversation,
)
from ...pg.domain.saved_pg_conversation import AiConversationBO


class AIConversationRepository:
    @staticmethod
    async def create(conversation_data: Dict[str, Any]) -> AIConversation:
        """创建新会话"""
        # 生成下一个ID
        return await AIConversation.create(**conversation_data)

    @staticmethod
    async def save_conversation(bo: AiConversationBO):
        return await AIConversation.create(**bo.model_dump())

    @staticmethod
    async def update(conversation_id: int, new_title: str) -> Optional[AIConversation]:
        """更新会话：目前只更新title，，，"""
        # 检查会话是否存在
        record = await AIConversation.get_or_none(
            id=conversation_id, deleted_at__isnull=True
        )

        if not record:
            return None
        # 执行更新
        # await AIRecommendConversation.filter(id=conversation_id).update(title=new_title,updated_at=datetime.now())
        await AIConversation.filter(id=conversation_id).update(
            title=new_title
        )  # 数据库自动填充更新时间
        await record.refresh_from_db()  # 刷新对象状态
        return record

    @staticmethod
    async def update_context(conversation_id: int, context: Dict[str, Any]):
        record = await AIConversation.get_or_none(
            id=conversation_id, deleted_at__isnull=True
        )

        if not record:
            return

        await AIConversation.filter(id=conversation_id).update(context=context)

        await record.refresh_from_db()

    @staticmethod
    async def delete(conversation_id: int) -> int:
        return await AIConversation.filter(id=conversation_id).delete()

    @staticmethod
    async def soft_delete(conversation_id: int) -> Optional[AIConversation]:
        """软删除（标记 deleted_at 字段）"""
        # 先检查记录是否存在
        record = await AIConversation.get_or_none(
            id=conversation_id, deleted_at__isnull=True
        )
        if not record:
            return None
        # 执行软删除
        await AIConversation.filter(id=conversation_id).update(
            deleted_at=datetime.now()
        )
        await record.refresh_from_db()  # 从数据库重新加载最新数据
        return record

    @staticmethod
    async def get_by_id(conversation_id: int) -> Optional[AIConversation]:
        return await AIConversation.get_or_none(id=conversation_id)

    # 通过用户id查会话列表
    @staticmethod
    async def get_by_uni_identity_id(
        uni_identity_id: str, identity_type: str
    ) -> Dict[str, Any]:
        items = (
            await AIConversation.filter(
                uni_identity_id=uni_identity_id,
                identity_type=identity_type,
                updated_at__isnull=False,
            )
            .all()
            .order_by("-updated_at")
        )
        return {"items": items, "has_more": "", "next_id": "", "prev_id": ""}

    @staticmethod
    async def count_conversations(conversation_id: str) -> int:
        return await AIConversation.filter(conversation_id=conversation_id).count()

    @staticmethod
    async def get_conversation_by_resume_id(resume_id: int) -> List[AiConversationBO]:
        """通过简历ID查询会话列表"""
        conversations = await AIConversation.filter(
            context__contains={"resume_id": resume_id}
        ).order_by("-created_at")

        return [
            AiConversationBO(**conversation.__dict__) for conversation in conversations
        ]

    @staticmethod
    async def get_conversation_by_interview_id(
        interview_id: str,
    ) -> List[AiConversationBO]:
        """通过面试ID查询会话列表"""
        conversations = await AIConversation.filter(
            context__contains={"interview_id": interview_id}
        ).order_by("-created_at")

        return [
            AiConversationBO(**conversation.__dict__) for conversation in conversations
        ]

    @staticmethod
    async def update_conversation_by_id(conversation_id: str, last_message: str):
        await AIConversation.filter(id=conversation_id).update(
            last_message=last_message
        )

    @staticmethod
    async def get_conversation_by_user_id_and_function_id(
        identity_id: str, identity_type: str, function_id: int
    ) -> List[AiConversationBO]:
        conversations = await AIConversation.filter(
            uni_identity_id=identity_id,
            identity_type=identity_type,
            context__contains={"function_id": function_id},
        )

        return [
            AiConversationBO(**conversation.__dict__) for conversation in conversations
        ]
