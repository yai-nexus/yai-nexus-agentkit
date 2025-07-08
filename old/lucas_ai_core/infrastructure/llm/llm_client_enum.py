from enum import Enum


class LLMClientEnum(Enum):
    """大模型类型枚举"""

    # 智谱AI模型
    ZHIPU_GLM_4_FLASH = ("glm-4-flash", "zhipu", "智谱AI GLM-4-Flash模型，快速版本")
    ZHIPU_GLM_4 = ("glm-4", "zhipu", "智谱AI GLM-4模型，标准版本")

    # 通义千问模型
    QWEN_32B = ("qwen2.5-32b-instruct", "qwen", "通义千问32B模型")
    QWEN_14B = ("qwen2.5-14b-instruct", "qwen", "通义千问14B模型")
    QWEN_7B = ("qwen2.5-7b-instruct", "qwen", "通义千问7B模型")
    QWEN3_235B = ("qwen3-235b-a22b", "qwen", "通义千问3 235B模型")
    QWEN3_32B = ("qwen3-32b", "qwen", "通义千问3 32B模型")
    QWEN3_14B = ("qwen3-14b", "qwen", "通义千问3 14B模型")

    QWEN3_PLUS_LATEST = ("qwen-plus-latest", "qwen", "通义千问3 qwen-plus-latest模型")
    QWEN3_TURBO_LATEST = (
        "qwen-turbo-latest",
        "qwen",
        "通义千问3 qwen-turbo-latest模型",
    )

    DOUBAO_1_5_PRO_256K = ("doubao-1-5-pro-256k-250115", "doubao", "doubao1.5pro模型")
    DOUBAO_1_5_THINKING_PRO = (
        "doubao-1-5-thinking-pro-250415",
        "doubao",
        "doubao1.5pro thinking 模型",
    )

    DOUBAO_SEED_1_6 = ("doubao-seed-1-6-250615", "doubao", "doubao 1.6模型")
    DOUBAO_SEED_1_6_THINKING = (
        "doubao-seed-1-6-thinking-250615",
        "doubao",
        "doubao1.6 thinking 模型",
    )

    # DeepSeek模型
    DEEPSEEK_EP = ("ep-20250214133443-wnff8", "deepseek", "DeepSeek模型")

    def __init__(self, model_name: str, llm: str, description: str):
        self.model_name = model_name
        self.llm = llm
        self.description = description

    @classmethod
    def get_model_name(cls, model_type: "LLMClientEnum") -> str:
        """获取模型名称"""
        return model_type.model_name

    @classmethod
    def get_model_config_key(cls, model_type: "LLMClientEnum") -> str:
        """获取模型配置键名"""
        return model_type.llm

    @classmethod
    def get_model_description(cls, model_type: "LLMClientEnum") -> str:
        """获取模型描述"""
        return model_type.description
