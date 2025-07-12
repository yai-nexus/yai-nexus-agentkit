"""
灵活的日志系统模块

基于 loguru 的现代化日志解决方案，提供：
- 策略模式的日志路径管理
- 链式配置接口
- 环境自适应配置
- 结构化日志输出
- 自动上下文追踪
- 优雅的错误处理

Usage:
    # 基本配置
    from yai_nexus_agentkit.core.logging import LoggerConfigurator, get_logger
    
    configurator = LoggerConfigurator().configure_console()
    logger = get_logger()
    logger.info("Application started")
    
    # 使用策略配置文件日志
    from your_app.strategies import HourlyDirectoryStrategy
    
    strategy = HourlyDirectoryStrategy()
    configurator = LoggerConfigurator().configure_console().configure_file(strategy)
    
    # 带上下文的日志
    logger = get_logger(contextual=True)
    logger.with_trace_id("abc123").info("Processing request")
"""

import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from loguru import logger as _logger


class LogPathStrategy(ABC):
    """日志路径生成策略抽象接口"""
    
    @abstractmethod
    def get_log_path(self, service_name: str) -> str:
        """生成日志文件路径"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """获取策略元数据（用于监控和调试）"""
        pass


class LoggerConfigurator:
    """日志配置器 - 提供灵活的日志配置能力"""
    
    def __init__(self, log_level: str = "INFO", service_name: str = "app", clean_start: bool = True):
        self.log_level = log_level
        self.service_name = service_name
        self._handlers = []
        
        # 清理默认处理器，确保干净的配置环境
        if clean_start:
            _logger.remove()
    
    def configure_console(self, 
                         format_template: Optional[str] = None,
                         colorize: bool = True) -> 'LoggerConfigurator':
        """配置控制台日志输出"""
        default_format = (
            "<green>{time:HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        _logger.add(
            sys.stderr,
            format=format_template or default_format,
            level=self.log_level,
            colorize=colorize,
            backtrace=True,
            diagnose=True,
            enqueue=False,
        )
        
        self._handlers.append("console")
        return self
    
    def configure_file(self,
                      path_strategy: LogPathStrategy,
                      format_template: Optional[str] = None,
                      serialize: bool = True,
                      rotation: str = "1 hour",
                      retention: str = "7 days",
                      **kwargs) -> 'LoggerConfigurator':
        """配置文件日志输出"""
        
        try:
            log_path = path_strategy.get_log_path(self.service_name)
            
            default_format = (
                "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | "
                "{name}:{function}:{line} | {message}"
            )
            
            _logger.add(
                log_path,
                format=format_template or default_format,
                level="DEBUG",
                rotation=rotation,
                retention=retention,
                serialize=serialize,
                backtrace=True,
                diagnose=True,
                enqueue=True,
                **kwargs
            )
            
            self._handlers.append(f"file:{log_path}")
            
            # 记录策略元数据
            metadata = path_strategy.get_metadata()
            _logger.info(f"File logging configured", 
                        extra={
                            "log_path": log_path,
                            "strategy": metadata.get("strategy_name", "unknown"),
                            "strategy_config": metadata
                        })
            
        except Exception as e:
            _logger.warning(f"Failed to setup file logging: {e}")
        
        return self
    
    def configure_development(self) -> 'LoggerConfigurator':
        """开发环境默认配置"""
        return self.configure_console(colorize=True)
    
    def configure_production(self) -> 'LoggerConfigurator':
        """生产环境默认配置"""
        return self.configure_console(colorize=False)
    
    def get_active_handlers(self) -> list:
        """获取已激活的日志处理器列表"""
        return self._handlers.copy()


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


def get_logger(name: Optional[str] = None, contextual: bool = False):
    """
    获取配置好的 logger 实例
    
    Args:
        name: logger 名称，通常传入 __name__
        contextual: 是否返回 ContextualLogger 包装实例
        
    Returns:
        Logger 实例（原生 loguru 或 ContextualLogger 包装）
    """
    base_logger = _logger
    if name:
        base_logger = _logger.bind(name=name)
    
    if contextual:
        return ContextualLogger(base_logger)
    return base_logger


def configure_logging() -> None:
    """配置全局日志系统，应用启动时调用一次（向后兼容）"""
    env = os.getenv("ENV", "development").lower()
    log_level = os.getenv("LOG_LEVEL", "DEBUG" if env == "development" else "INFO").upper()
    
    configurator = LoggerConfigurator(log_level=log_level, clean_start=True)
    
    if env in ("production", "prod"):
        configurator.configure_production()
    else:
        configurator.configure_development()
    
    # 记录配置信息
    _logger.info(
        "Logging system configured (legacy mode)", 
        env=env,
        level=log_level,
        handlers=configurator.get_active_handlers()
    )


# 自动配置（导入时执行，向后兼容）
configure_logging()

# 导出默认 logger 实例（向后兼容）
logger = get_logger(contextual=True)

# 导出的公共接口
__all__ = [
    'LoggerConfigurator', 
    'LogPathStrategy', 
    'ContextualLogger',
    'get_logger',
    'configure_logging',  # 向后兼容
    'logger'  # 向后兼容
]