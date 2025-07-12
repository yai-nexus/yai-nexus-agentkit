"""
统一日志系统模块

基于 loguru 的现代化日志解决方案，提供：
- 环境自适应配置（开发/生产）
- 结构化日志输出
- 自动上下文追踪
- 优雅的错误处理

Usage:
    from yai_nexus_agentkit.core.logging import logger
    
    # 基本使用
    logger.info("Application started")
    
    # 带上下文的日志
    logger.bind(trace_id="abc123", user_id="user456").info("Processing request")
    
    # 上下文管理器模式
    with logger.contextualize(trace_id="abc123"):
        logger.info("This will include trace_id automatically")
"""

import os
import sys
from typing import Optional, Dict, Any
from loguru import logger as _logger


class LoggerConfigurator:
    """loguru 日志配置管理器"""
    
    def __init__(self):
        self.env = os.getenv("ENV", "development").lower()
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG" if self.env == "development" else "INFO").upper()
        self.is_production = self.env in ("production", "prod")
        
    def configure(self) -> None:
        """配置 loguru logger"""
        # 移除默认handler
        _logger.remove()
        
        if self.is_production:
            self._configure_production()
        else:
            self._configure_development()
            
    def _configure_production(self) -> None:
        """生产环境配置：JSON格式，结构化输出"""
        _logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name} | {function}:{line} | {extra[trace_id]:-} | {message}",
            level=self.log_level,
            serialize=True,  # JSON 输出
            backtrace=True,
            diagnose=False,  # 生产环境不暴露变量值
            enqueue=True,    # 异步写入
        )
        
        # 文件日志（可选）
        log_file = os.getenv("LOG_FILE")
        if log_file:
            _logger.add(
                log_file,
                rotation="100 MB",
                retention="30 days",
                compression="gz",
                level=self.log_level,
                serialize=True,
                backtrace=True,
                diagnose=False,
                enqueue=True,
            )
    
    def _configure_development(self) -> None:
        """开发环境配置：美化输出，带颜色"""
        _logger.add(
            sys.stderr,
            format=(
                "<green>{time:HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<magenta>{extra[trace_id]:-}</magenta> | "
                "<level>{message}</level>"
            ),
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,  # 开发环境显示变量值
            enqueue=False,  # 同步写入，便于调试
        )


class ContextualLogger:
    """支持上下文的 Logger 包装器"""
    
    def __init__(self, base_logger=None):
        self._logger = base_logger or _logger
        self._context: Dict[str, Any] = {}
    
    def bind(self, **kwargs) -> "ContextualLogger":
        """绑定上下文信息，返回新的 logger 实例"""
        new_context = {**self._context, **kwargs}
        bound_logger = self._logger.bind(**new_context)
        return ContextualLogger(bound_logger)
    
    def contextualize(self, **kwargs):
        """上下文管理器，自动绑定和清理上下文"""
        return self._logger.contextualize(**kwargs)
    
    def with_trace_id(self, trace_id: str) -> "ContextualLogger":
        """便捷方法：绑定 trace_id"""
        return self.bind(trace_id=trace_id)
    
    def with_request_id(self, request_id: str) -> "ContextualLogger":
        """便捷方法：绑定 request_id"""
        return self.bind(request_id=request_id)
    
    def with_user_id(self, user_id: str) -> "ContextualLogger":
        """便捷方法：绑定 user_id"""
        return self.bind(user_id=user_id)
    
    # 代理所有 loguru 方法
    def trace(self, message: str, *args, **kwargs):
        return self._logger.trace(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        return self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        return self._logger.info(message, *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        return self._logger.success(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        return self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        return self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        return self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        return self._logger.exception(message, *args, **kwargs)
    
    def catch(self, *args, **kwargs):
        """异常捕获装饰器"""
        return self._logger.catch(*args, **kwargs)
    
    def add(self, *args, **kwargs):
        """添加新的 handler"""
        return self._logger.add(*args, **kwargs)
    
    def remove(self, *args, **kwargs):
        """移除 handler"""
        return self._logger.remove(*args, **kwargs)


def get_logger(name: Optional[str] = None) -> ContextualLogger:
    """
    获取配置好的 logger 实例
    
    Args:
        name: logger 名称，通常传入 __name__
        
    Returns:
        ContextualLogger: 支持上下文的 logger 实例
    """
    if name:
        bound_logger = _logger.bind(name=name)
        return ContextualLogger(bound_logger)
    return ContextualLogger(_logger)


def configure_logging() -> None:
    """配置全局日志系统，应用启动时调用一次"""
    configurator = LoggerConfigurator()
    configurator.configure()
    
    # 记录配置信息
    _logger.info(
        "Logging system configured", 
        env=configurator.env,
        level=configurator.log_level,
        production=configurator.is_production
    )


# 自动配置（导入时执行）
configure_logging()

# 导出默认 logger 实例
logger = get_logger()

__all__ = [
    "logger",
    "get_logger", 
    "configure_logging",
    "ContextualLogger",
    "LoggerConfigurator"
]