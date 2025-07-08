# -*- coding: utf-8 -*-
"""应用核心业务逻辑模块。"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage


class ChatService:
    """
    聊天服务，封装了核心的业务逻辑。
    """

    def __init__(self, llm: BaseChatModel):
        """
        初始化聊天服务。

        Args:
            llm: 一个继承自 LangChain BaseChatModel 的语言模型客户端实例。
        """
        # 服务依赖于 LangChain 的抽象基类，而不是任何具体的实现。
        self._llm = llm

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
