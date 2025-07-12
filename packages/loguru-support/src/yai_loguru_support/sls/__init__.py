"""
Aliyun SLS (Simple Log Service) integration for loguru.

This module provides production-ready integration with Aliyun SLS,
using the official aliyun-log-python-sdk for maximum reliability.
"""

try:
    from .sink import AliyunSlsSink, SlsConfig
    __all__ = ["AliyunSlsSink", "SlsConfig"]
except ImportError as e:
    raise ImportError(
        "aliyun-log-python-sdk is required for SLS support. "
        "Install with: pip install yai-loguru-support[sls]"
    ) from e