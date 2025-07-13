"""
日志策略模块

提供不同的日志存储策略，包括：
- HourlyDirectoryStrategy: 按小时分目录存储日志
- DailyDirectoryStrategy: 按天分目录存储日志
- SimpleFileStrategy: 简单文件存储策略

这些策略与统一日志配置系统配合使用。
"""

from .directory_strategies import (
    HourlyDirectoryStrategy,
    DailyDirectoryStrategy,
    SimpleFileStrategy
)

__all__ = [
    "HourlyDirectoryStrategy",
    "DailyDirectoryStrategy", 
    "SimpleFileStrategy"
]