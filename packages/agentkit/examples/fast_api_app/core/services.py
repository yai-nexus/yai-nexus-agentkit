# -*- coding: utf-8 -*-
"""应用核心业务逻辑模块。"""

from langchain_core.messages import HumanMessage
from typing import List, Optional
import uuid

from yai_nexus_agentkit.core.repository import BaseRepository
from yai_nexus_agentkit.llm import LLMFactory
from yai_nexus_agentkit.persistence import PostgresCheckpoint
from yai_nexus_agentkit.persistence.models import AgentConversation


class ChatService:
    """
    聊天服务，封装了核心的业务逻辑。
    """

    def __init__(self, llm_factory: LLMFactory, checkpoint_repo: PostgresCheckpoint):
        """
        初始化聊天服务。

        Args:
            llm_factory: LLM 工厂实例
            checkpoint_repo: Checkpoint 仓储实例
        """
        self._llm_factory = llm_factory
        self._checkpoint_repo = checkpoint_repo
        # For simplicity, get a default LLM client.
        # In a real app, you might select one based on the conversation or request.
        self._llm = self._llm_factory.get_llm_client("default_openai")

    async def get_reply(self, prompt: str) -> str:
        """
        根据用户输入获取 AI 回复。

        Args:
            prompt: 用户的输入。

        Returns:
            AI 的回复字符串。
        """
        # 在这里可以添加更复杂的业务逻辑，例如处理聊天记录等。
        # 我们将用户的输入包装成 LangChain 的 HumanMessage 对象。
        message = HumanMessage(content=prompt)

        # 使用 LangChain 的 ainvoke 方法进行调用。
        ai_message = await self._llm.ainvoke([message])

        # 返回消息内容
        return ai_message.content


class ConversationService:
    """
    对话服务，封装了对话的 CRUD 逻辑。
    """

    def __init__(self, repo: BaseRepository[AgentConversation]):
        """
        初始化对话服务。

        Args:
            repo: 对话仓储实例。
        """
        self._repo = repo

    async def get_conversation(self, convo_id: str) -> Optional[AgentConversation]:
        """
        获取对话。

        Args:
            convo_id: 对话 ID

        Returns:
            对话实例或 None
        """
        return await self._repo.get(convo_id)

    async def create_conversation(
        self, title: str = None, metadata: dict = None
    ) -> AgentConversation:
        """
        创建对话。

        Args:
            title: 对话标题
            metadata: 元数据

        Returns:
            已创建的对话实例
        """
        conversation = AgentConversation(
            id=uuid.uuid4(),
            checkpoint_thread_id=uuid.uuid4(),
            title=title,
            metadata_=metadata,
        )
        return await self._repo.add(conversation)

    async def list_conversations(
        self, limit: int = 100, offset: int = 0
    ) -> List[AgentConversation]:
        """
        列出对话。

        Args:
            limit: 最大返回数量
            offset: 跳过数量

        Returns:
            对话列表
        """
        return await self._repo.list(limit=limit, offset=offset)

    async def update_conversation(
        self, convo_id: str, title: str = None, metadata: dict = None
    ) -> Optional[AgentConversation]:
        """
        更新对话。

        Args:
            convo_id: 对话 ID
            title: 对话标题
            metadata: 元数据

        Returns:
            已更新的对话实例或 None
        """
        conversation = await self._repo.get(convo_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if metadata is not None:
            conversation.metadata_ = metadata

        return await self._repo.update(conversation)

    async def delete_conversation(self, convo_id: str) -> bool:
        """
        删除对话。

        Args:
            convo_id: 对话 ID

        Returns:
            删除成功返回 True，否则返回 False
        """
        return await self._repo.delete(convo_id)

    async def count_conversations(self) -> int:
        """
        统计对话数量。

        Returns:
            对话数量
        """
        return await self._repo.count()
