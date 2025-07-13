"""
统一日志配置模块

提供与 pino-support 语义一致的高级配置函数，实现跨技术栈的统一日志管理体验。

配置接口遵循 pino-support 中定义的 LoggerConfig TypeScript 接口规范。
"""

import sys
from typing import Dict, Any, Optional, Union
from loguru import logger
from pathlib import Path

from .strategies import HourlyDirectoryStrategy, DailyDirectoryStrategy, SimpleFileStrategy


# 默认配置，与 pino-support 的 LoggerConfig 接口保持语义一致
DEFAULT_CONFIG = {
    "level": "info",
    "console": {
        "enabled": True,
        "pretty": True
    },
    "file": {
        "enabled": True,
        "baseDir": "logs",
        "strategy": "hourly",
        "maxSize": None,
        "maxFiles": None
    },
    "cloud": {
        "enabled": False,
        "sls": None
    }
}


def setup_logging(service_name: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    统一日志配置函数
    
    根据配置对象设置 loguru 日志记录器，包括控制台输出和文件输出。
    配置结构与 pino-support 的 LoggerConfig 接口保持一致。
    
    Args:
        service_name: 服务名称，用于日志文件命名和标识
        config: 日志配置对象，结构遵循 TypeScript LoggerConfig 接口
                如果为 None，将使用默认配置
    
    Examples:
        # 使用默认配置
        setup_logging("my-service")
        
        # 自定义配置
        setup_logging("my-service", {
            "level": "debug",
            "console": {"enabled": True, "pretty": False},
            "file": {"enabled": True, "strategy": "daily"}
        })
        
        # 禁用文件日志
        setup_logging("my-service", {
            "file": {"enabled": False}
        })
    """
    # 合并配置
    final_config = _merge_config(DEFAULT_CONFIG, config or {})
    
    # 移除所有现有的处理器
    logger.remove()
    
    # 设置控制台输出
    if final_config["console"]["enabled"]:
        _setup_console_logging(final_config)
    
    # 设置文件输出
    if final_config["file"]["enabled"]:
        _setup_file_logging(service_name, final_config)
    
    # 注意：不要重置处理器，否则会清空刚刚添加的处理器


def _merge_config(default: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并配置对象"""
    result = default.copy()
    
    for key, value in user_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def _setup_console_logging(config: Dict[str, Any]) -> None:
    """设置控制台日志输出"""
    level = config["level"].upper()
    pretty = config["console"].get("pretty", True)
    
    if pretty:
        # 开发友好的格式
        format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    else:
        # 生产环境的 JSON 格式
        format_str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    
    logger.add(
        sys.stderr,
        format=format_str,
        level=level,
        colorize=pretty,
        serialize=False
    )


def _setup_file_logging(service_name: str, config: Dict[str, Any]) -> None:
    """设置文件日志输出"""
    level = config["level"].upper()
    file_config = config["file"]
    
    # 选择目录策略
    strategy_name = file_config.get("strategy", "hourly")
    base_dir = file_config.get("baseDir", "logs")
    
    if strategy_name == "hourly":
        strategy = HourlyDirectoryStrategy(
            base_dir=base_dir,
            create_symlink=True,
            create_readme=True
        )
    elif strategy_name == "daily":
        strategy = DailyDirectoryStrategy(
            base_dir=base_dir,
            create_symlink=True
        )
    else:
        # 回退到简单文件策略
        strategy = SimpleFileStrategy(
            log_dir=base_dir,
            filename_template=f"{service_name}.log"
        )
    
    # 获取日志文件路径
    log_path = strategy.get_log_path(service_name)
    
    # 配置文件输出参数
    file_kwargs = {
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        "level": level,
        "serialize": False,  # 使用结构化格式而不是 JSON
        "enqueue": True,     # 异步写入
        "catch": True        # 捕获异常
    }
    
    # 添加文件大小和轮转配置
    if file_config.get("maxSize"):
        file_kwargs["rotation"] = file_config["maxSize"]
    
    if file_config.get("maxFiles"):
        file_kwargs["retention"] = file_config["maxFiles"]
    else:
        file_kwargs["retention"] = "7 days"  # 默认保留 7 天
    
    logger.add(log_path, **file_kwargs)


def get_logger_metadata(service_name: str) -> Dict[str, Any]:
    """
    获取当前日志配置的元数据信息
    
    Args:
        service_name: 服务名称
        
    Returns:
        包含日志配置元数据的字典
    """
    return {
        "service_name": service_name,
        "package_name": "yai-loguru-support",
        "logger_type": "loguru",
        "handlers_count": len(logger._core.handlers),
        "min_level": min([handler._levelno for handler in logger._core.handlers.values()]) if logger._core.handlers else 0
    }


# 便利函数，用于快速设置常见配置
def setup_dev_logging(service_name: str) -> None:
    """开发环境日志配置 - 控制台美化输出 + 文件记录"""
    setup_logging(service_name, {
        "level": "debug",
        "console": {"enabled": True, "pretty": True},
        "file": {"enabled": True, "strategy": "hourly"}
    })


def setup_prod_logging(service_name: str, log_level: str = "info") -> None:
    """生产环境日志配置 - JSON 格式 + 文件轮转"""
    setup_logging(service_name, {
        "level": log_level,
        "console": {"enabled": True, "pretty": False},
        "file": {"enabled": True, "strategy": "hourly"}
    })


def setup_console_only_logging(service_name: str, log_level: str = "info") -> None:
    """仅控制台日志 - 适用于 CI/CD 或容器环境"""
    setup_logging(service_name, {
        "level": log_level,
        "console": {"enabled": True, "pretty": False},
        "file": {"enabled": False}
    })


__all__ = [
    "setup_logging",
    "setup_dev_logging", 
    "setup_prod_logging",
    "setup_console_only_logging",
    "get_logger_metadata"
]