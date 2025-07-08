#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Nero Claudius
@date: 2025/4/14
@version: 0.0.1
"""

from typing import Optional

from lucas_common_components.nacos.annotate.config_annotate import nacos_config
from lucas_common_components.nacos.model.base_config import LucasBaseConfig
from pydantic import Field, BaseModel


class LangfuseConfig(BaseModel):
    public_key: str = Field(default="", description="public_key")
    secret_key: str = Field(default="", description="secret_key")
    url: str = Field(default="", description="url")


class LLMConfig(BaseModel):
    api_key: str = Field(default="", description="api_key")
    api_base: str = Field(default="", description="api_base")


@nacos_config(data_id="LLMNacosConfig", group="PYTHON")
class LLMNacosConfig(LucasBaseConfig):
    zhipu: Optional[LLMConfig] = None
    doubao: Optional[LLMConfig] = None
    qwen: Optional[LLMConfig] = None
    openai: Optional[LLMConfig] = None
    deepseek: Optional[LLMConfig] = None
