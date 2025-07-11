#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional

from yai_nexus_configuration import NexusConfig, nexus_config


class LLMConfig(NexusConfig):
    """Represents the configuration for a single LLM."""

    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@nexus_config(data_id="llms.json")
class AllLLMConfigs(NexusConfig):
    """Represents the container for all LLM configurations."""

    llms: List[LLMConfig]
