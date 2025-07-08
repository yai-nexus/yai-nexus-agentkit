# -*- coding: utf-8 -*-
"""应用配置模块。"""
from pydantic_settings import BaseSettings, SettingsConfigDict

from yai_nexus_agentkit.infrastructure.llm.openai import OpenAIConfig


class AppSettings(BaseSettings):
    """
    应用配置类，使用 pydantic-settings 从环境变量加载配置。
    """
    OPENROUTER_API_KEY: str = "YOUR_API_KEY_HERE"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding='utf-8',
        extra="ignore"
    )

    @property
    def openai_config(self) -> OpenAIConfig:
        """
        创建并返回适用于 OpenRouter 的配置对象。

        Returns:
            一个 OpenAIConfig 实例。
        """
        return OpenAIConfig(
            api_key=self.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )


# 创建一个全局的配置实例，供整个应用使用。
settings = AppSettings()
