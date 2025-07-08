from typing import List, Optional, Dict, Any

from tortoise.expressions import Q

from ..domain.saved_pg_message import AiMessageBO
from ..models.ai_message import AiMessage


class AiMessageRepository:
    @staticmethod
    async def create(conversation_data: dict) -> AiMessage:
        return await AiMessage.create(**conversation_data)

    @staticmethod
    async def save_message(bo: AiMessageBO) -> AiMessage:
        return await AiMessage.create(**bo.model_dump())

    @staticmethod
    async def update(conversation_id: int, update_data: dict) -> list[AiMessage]:
        await AiMessage.filter(id=conversation_id).update(**update_data)
        return await AiMessageRepository.get_by_id(conversation_id)

    @staticmethod
    async def delete(conversation_id: int) -> int:
        return await AiMessage.filter(id=conversation_id).delete()

    @staticmethod
    async def get_by_id(conversation_id: str) -> List[AiMessage]:
        return (
            await AiMessage.filter(conversation_id=conversation_id)
            .all()
            .order_by("created_at")
        )

    @staticmethod
    async def get_by_id_prev(
        conversation_id: str, id: Optional[str] = None, page_size: int = 10
    ) -> Dict[str, Any]:
        """
        通过会话ID查询消息列表，支持基于ID的分页
        Args:
            conversation_id: 会话ID
            id: 游标ID，用于分页
            page_size: 每页数量
        Returns:
            Dict包含:
            - items: 当前页的消息列表
            - has_more: 是否还有更多数据
            - next_id: 下一页的游标ID
            - prev_id: 上一页的游标ID
        """
        base_query = AiMessage.filter(conversation_id=conversation_id).order_by(
            "-id"
        )  # 改为降序，先显示最新消息

        if id:
            items = await base_query.filter(id__lt=id).limit(page_size + 1)
        else:
            items = await base_query.limit(page_size + 1)

        has_more = len(items) > page_size
        if has_more:
            items = items[:-1]

        next_id = items[-1].id if items else None
        prev_id = items[0].id if items else None

        return {
            "items": items,
            "has_more": has_more,
            "next_id": next_id,
            "prev_id": prev_id,
        }

    @staticmethod
    async def get_last_message_by_conversation_id(
        conversation_id: str,
    ) -> Optional[AiMessage]:
        return (
            await AiMessage.filter(conversation_id=conversation_id)
            .order_by("created_at")
            .last()
        )

    @staticmethod
    async def get_by_biz_key(biz_key: str) -> Optional[AiMessage]:
        return await AiMessage.get_or_none(biz_key=biz_key)

    @staticmethod
    async def get_by_user_id(uni_user_id: str) -> List[AiMessage]:
        return await AiMessage.filter(uni_user_id=uni_user_id).all()

    @staticmethod
    async def get_by_staff_id(uni_staff_id: str) -> List[AiMessage]:
        return await AiMessage.filter(uni_staff_id=uni_staff_id).all()

    @staticmethod
    async def get_by_tenant_id(uni_tenant_id: str) -> List[AiMessage]:
        return await AiMessage.filter(uni_tenant_id=uni_tenant_id).all()
