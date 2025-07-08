# -*- coding: utf-8 -*-
"""应用核心业务逻辑模块。"""
from yai_nexus_agentkit.core.llm import BaseLLM


class ChatService:
    """
    聊天服务，封装了核心的业务逻辑。
    """
    def __init__(self, llm: BaseLLM):
        """
        初始化聊天服务。

        Args:
            llm: 一个实现了 BaseLLM 接口的语言模型客户端实例。
        """
        # 服务依赖于 ABC，而不是具体的实现，这体现了依赖倒置原则。
        self._llm = llm

    async def get_reply(self, prompt: str) -> str:
        """
        根据用户输入获取 AI 回复。

        Args:
            prompt: 用户的输入。

        Returns:
            AI 的回复。
        """
        # 在这里可以添加更复杂的业务逻辑
        # 我们在这里硬编码模型，以使用 OpenRouter 上的 Claude 3.5 Sonnet
        response = await self._llm.ask(prompt, model="anthropic/claude-3.5-sonnet")
        return f"AI: {response}" 