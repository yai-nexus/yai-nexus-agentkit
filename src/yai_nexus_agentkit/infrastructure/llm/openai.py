# -*- coding: utf-8 -*-
"""OpenAI 模块提供了与 OpenAI API 对接的客户端实现。"""
from pydantic import BaseModel, Field
from typing import Optional


class OpenAIConfig(BaseModel):
    """
    OpenAIClient 的配置模型。
    """
    api_key: str = Field(..., description="OpenAI API 密钥。")
    base_url: str = Field("https://api.openai.com/v1", description="OpenAI API 的基础 URL。")


from yai_nexus_agentkit.core.llm import BaseLLM
from openai import AsyncOpenAI


class OpenAIClient(BaseLLM):
    """
    OpenAI 语言模型的客户端实现。
    """

    def __init__(self, config: OpenAIConfig):
        """
        初始化 OpenAIClient。

        Args:
            config: OpenAIClient 的配置对象。
        """
        self.config = config
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    async def ask(self, prompt: str, model: Optional[str] = "gpt-3.5-turbo") -> str:
        """
        使用 OpenAI API 向语言模型发送提示并获取回复。

        Args:
            prompt: 发送给语言模型的提示字符串。
            model: 要使用的模型名称。默认为 "gpt-3.5-turbo"。

        Returns:
            来自语言模型的回复字符串。
        """
        model_to_use = model or "gpt-3.5-turbo"
        chat_completion = await self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_to_use,
        )
        return chat_completion.choices[0].message.content 