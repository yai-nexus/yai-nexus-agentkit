import asyncio
import os
import uuid
from typing import (
    Any,
    Optional,
    Tuple,
    Union,
)

from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler
from lucas_ai_core.infrastructure.snow_flake import Snowflake
from lucas_common_components.logging import setup_logger
from pydantic import SecretStr

from .llm_client_enum import LLMClientEnum
from .llm_model import LLMNacosConfig

logger = setup_logger(name=__name__, level="DEBUG")

sf = Snowflake(worker_id=0, datacenter_id=0)

# 添加LLM实例缓存
_llm_cache = {}
_llm_cache_lock = asyncio.Lock()


def get_llm_config(llm):
    if llm == "qwen":
        return LLMNacosConfig.get_instance().qwen
    elif llm == "zhipu":
        return LLMNacosConfig.get_instance().zhipu
    elif llm == "doubao":
        return LLMNacosConfig.get_instance().doubao
    elif llm == "deepseek":
        return LLMNacosConfig.get_instance().deepseek

    else:
        raise ValueError(f"Unknown LLM: {llm}")
    pass


class LLMClientUtils:
    @classmethod
    def __get_langfuse_callback(
        cls,
        session_id: Optional[str] = None,
        session_id_generator: Optional[callable] = None,
    ):
        """Get Langfuse callback handler with customizable session ID

        Args:
            session_id (str, optional): Direct session ID string. If provided, this takes precedence.
            session_id_generator (callable, optional): A function that generates a session ID.
                                                     Defaults to UUID generator if session_id is not provided.
        """
        # 从环境变量获取Langfuse配置
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST")

        if not public_key or not secret_key or not host:
            raise ValueError(
                "Missing Langfuse environment variables: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST"
            )

        # 确定使用哪个session ID
        if session_id is not None:
            final_session_id = session_id
        elif session_id_generator is not None:
            final_session_id = session_id_generator()
        else:
            final_session_id = str(uuid.uuid4())

        return CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            session_id=final_session_id,
            debug=False,
        )

    @classmethod
    def __create_llm_internal(
        cls,
        model_name: str,
        api_key: str,
        api_base: str,
        temperature: float = 0.7,
        streaming: bool = False,
        session_id: Optional[str] = None,
        session_id_generator: Optional[callable] = None,
    ) -> ChatOpenAI:
        """创建LLM实例的内部方法"""
        cache_key = f"{model_name}_{temperature}_{streaming}"

        if cache_key in _llm_cache:
            return _llm_cache[cache_key]

        try:
            llm = ChatOpenAI(
                temperature=temperature,
                model_name=model_name,
                openai_api_key=SecretStr(api_key),
                openai_api_base=api_base,
                verbose=True,
                streaming=streaming,
                request_timeout=600,
                max_retries=3,
            )

            # 检查是否存在Langfuse环境变量
            if (
                os.getenv("LANGFUSE_PUBLIC_KEY")
                and os.getenv("LANGFUSE_SECRET_KEY")
                and os.getenv("LANGFUSE_HOST")
            ):
                handler = cls.__get_langfuse_callback(
                    session_id=session_id, session_id_generator=session_id_generator
                )
                llm.callbacks = [handler]

            # 限制缓存大小
            if len(_llm_cache) > 10:
                oldest_key = next(iter(_llm_cache))
                del _llm_cache[oldest_key]

            _llm_cache[cache_key] = llm
            return llm
        except Exception as e:
            logger.error(f"Error creating LLM: {str(e)}", exc_info=True)
            raise

    @classmethod
    async def __async_create_llm_v2(
        cls,
        model_type: LLMClientEnum,
        request_timeout: Union[float, Tuple[float, float], Any, None],
        session_id: Optional[str] = None,
        session_id_generator: Optional[callable] = None,
        max_retries: Optional[int] = None,
        streaming: bool = False,
        temperature: float = 0.7,
    ):
        """异步创建LLM实例"""
        model_name = model_type.model_name

        cache_key = f"{model_name}_{temperature}_{streaming}"

        llm_config = get_llm_config(model_type.llm)
        async with _llm_cache_lock:
            if cache_key in _llm_cache:
                return _llm_cache[cache_key]

            try:
                llm = ChatOpenAI(
                    temperature=temperature,
                    model_name=model_name,
                    openai_api_key=SecretStr(llm_config.api_key),
                    openai_api_base=llm_config.api_base,
                    verbose=True,
                    streaming=streaming,
                    request_timeout=request_timeout,
                    max_retries=max_retries,
                )

                # 检查是否存在Langfuse环境变量
                if (
                    os.getenv("LANGFUSE_PUBLIC_KEY")
                    and os.getenv("LANGFUSE_SECRET_KEY")
                    and os.getenv("LANGFUSE_HOST")
                ):
                    handler = cls.__get_langfuse_callback(
                        session_id=session_id, session_id_generator=session_id_generator
                    )
                    llm.callbacks = [handler]

                # 限制缓存大小
                if len(_llm_cache) > 10:
                    oldest_key = next(iter(_llm_cache))
                    del _llm_cache[oldest_key]

                _llm_cache[cache_key] = llm
                return llm
            except Exception as e:
                logger.error(f"Error creating LLM: {str(e)}", exc_info=True)
                raise

    @classmethod
    async def async_create_llm(
        cls,
        model_type: LLMClientEnum,
        streaming: bool = False,
        temperature: float = 0.7,
        session_id: Optional[str] = None,
        session_id_generator: Optional[callable] = None,
    ):
        return await cls.__async_create_llm_v2(
            model_type,
            request_timeout=60,
            max_retries=3,
            streaming=streaming,
            temperature=temperature,
            session_id=session_id,
            session_id_generator=session_id_generator,
        )

    @classmethod
    def create_llm(
        cls,
        model_type: LLMClientEnum,
        streaming: bool = False,
        temperature: float = 0.7,
        session_id: Optional[str] = None,
        session_id_generator: Optional[callable] = None,
    ) -> ChatOpenAI:
        """同步获取LLM实例"""
        llm_config = get_llm_config(model_type.llm)
        return cls.__create_llm_internal(
            model_name=model_type.model_name,
            api_key=llm_config.api_key,
            api_base=llm_config.api_base,
            streaming=streaming,
            temperature=temperature,
            session_id=session_id,
            session_id_generator=session_id_generator,
        )
