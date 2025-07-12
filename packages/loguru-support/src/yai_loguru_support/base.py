"""
Base classes and interfaces for loguru sinks.

This module provides the foundation for all cloud logging service integrations,
ensuring consistent behavior and standardized configuration across different providers.
"""

import abc
import asyncio
import threading
import time
from typing import Any, Dict, Optional, Union, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging

from loguru import logger as _logger


class SinkError(Exception):
    """Base exception for all sink-related errors."""
    pass


class SinkConnectionError(SinkError):
    """Raised when sink fails to connect to the remote service."""
    pass


class SinkConfigurationError(SinkError):
    """Raised when sink configuration is invalid."""
    pass


@dataclass
class SinkConfig:
    """Base configuration for all sinks."""
    
    # 基础配置
    level: str = "INFO"
    serialize: bool = True
    
    # 性能配置
    max_workers: int = 4
    queue_size: int = 10000
    batch_size: int = 100
    flush_interval: float = 5.0
    
    # 可靠性配置
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    # 监控配置
    enable_metrics: bool = True
    health_check_interval: float = 60.0
    
    # 自定义字段
    extra_fields: Dict[str, Any] = field(default_factory=dict)


class SinkMetrics:
    """Metrics collector for sink performance monitoring."""
    
    def __init__(self):
        self.reset()
        
    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.logs_sent = 0
        self.logs_failed = 0
        self.bytes_sent = 0
        self.connection_errors = 0
        self.last_error = None
        self.last_success = None
        self.start_time = time.time()
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.logs_sent + self.logs_failed
        if total == 0:
            return 100.0
        return (self.logs_sent / total) * 100.0
        
    @property
    def uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time
        
    def record_success(self, size: int = 0) -> None:
        """Record a successful log transmission."""
        self.logs_sent += 1
        self.bytes_sent += size
        self.last_success = time.time()
        
    def record_failure(self, error: Exception) -> None:
        """Record a failed log transmission."""
        self.logs_failed += 1
        self.last_error = error
        
    def record_connection_error(self) -> None:
        """Record a connection error."""
        self.connection_errors += 1
        
    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "logs_sent": self.logs_sent,
            "logs_failed": self.logs_failed,
            "bytes_sent": self.bytes_sent,
            "connection_errors": self.connection_errors,
            "success_rate": self.success_rate,
            "uptime": self.uptime,
            "last_error": str(self.last_error) if self.last_error else None,
            "last_success": self.last_success,
        }


class BaseSink(abc.ABC):
    """
    Abstract base class for all loguru sinks.
    
    Provides common functionality including:
    - Asynchronous log transmission
    - Batch processing
    - Error handling and retries
    - Performance metrics
    - Health checking
    - Graceful shutdown
    """
    
    def __init__(self, config: SinkConfig):
        self.config = config
        self.metrics = SinkMetrics()
        self._running = False
        self._queue: Optional[asyncio.Queue] = None
        self._background_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self._lock = threading.Lock()
        
        # Health check
        self._last_health_check = time.time()
        self._healthy = True
        
        # Logging setup
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup internal logging for the sink."""
        self._internal_logger = logging.getLogger(f"yai_loguru_support.{self.__class__.__name__}")
        if not self._internal_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._internal_logger.addHandler(handler)
            self._internal_logger.setLevel(logging.INFO)
            
    async def start(self) -> None:
        """Start the sink's background processing."""
        if self._running:
            return
            
        self._running = True
        self._queue = asyncio.Queue(maxsize=self.config.queue_size)
        
        # Start background processing task
        self._background_task = asyncio.create_task(self._background_worker())
        
        # Initialize the connection
        try:
            await self._initialize_connection()
            self._internal_logger.info(f"{self.__class__.__name__} started successfully")
        except Exception as e:
            self._running = False
            self.metrics.record_connection_error()
            self._internal_logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise SinkConnectionError(f"Failed to initialize sink: {e}") from e
            
    async def stop(self) -> None:
        """Stop the sink and flush remaining logs."""
        if not self._running:
            return
            
        self._internal_logger.info(f"Stopping {self.__class__.__name__}...")
        self._running = False
        
        # Wait for queue to be processed
        if self._queue:
            await self._queue.join()
            
        # Cancel background task
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
                
        # Cleanup connection
        try:
            await self._cleanup_connection()
        except Exception as e:
            self._internal_logger.error(f"Error during cleanup: {e}")
            
        # Shutdown executor
        self._executor.shutdown(wait=True)
        self._internal_logger.info(f"{self.__class__.__name__} stopped")
        
    def write(self, message: str) -> None:
        """
        Loguru sink entry point.
        
        This method is called by loguru for each log record.
        It queues the message for asynchronous processing.
        """
        if not self._running or not self._queue:
            return
            
        try:
            # Non-blocking queue put
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            self.metrics.record_failure(Exception("Queue full"))
            self._internal_logger.warning("Log queue is full, dropping message")
            
    async def _background_worker(self) -> None:
        """Background task that processes the log queue."""
        batch = []
        last_flush = time.time()
        
        while self._running or (self._queue and not self._queue.empty()):
            try:
                # Health check
                await self._periodic_health_check()
                
                # Try to get a message with timeout
                try:
                    message = await asyncio.wait_for(
                        self._queue.get(), 
                        timeout=self.config.flush_interval
                    )
                    batch.append(message)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    pass
                    
                # Check if we should flush the batch
                should_flush = (
                    len(batch) >= self.config.batch_size or
                    (batch and time.time() - last_flush >= self.config.flush_interval)
                )
                
                if should_flush and batch:
                    await self._flush_batch(batch)
                    batch.clear()
                    last_flush = time.time()
                    
            except Exception as e:
                self._internal_logger.error(f"Error in background worker: {e}")
                await asyncio.sleep(1)  # Prevent tight error loop
                
    async def _flush_batch(self, messages: list[str]) -> None:
        """Flush a batch of messages to the remote service."""
        for attempt in range(self.config.max_retries + 1):
            try:
                size = await self._send_batch(messages)
                self.metrics.record_success(size)
                return
            except Exception as e:
                self.metrics.record_failure(e)
                self._internal_logger.warning(
                    f"Attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    self._internal_logger.error(
                        f"Failed to send batch after {self.config.max_retries + 1} attempts"
                    )
                    
    async def _periodic_health_check(self) -> None:
        """Perform periodic health checks."""
        now = time.time()
        if now - self._last_health_check >= self.config.health_check_interval:
            self._last_health_check = now
            try:
                self._healthy = await self._health_check()
                if not self._healthy:
                    self._internal_logger.warning("Health check failed")
            except Exception as e:
                self._healthy = False
                self._internal_logger.error(f"Health check error: {e}")
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current sink metrics."""
        metrics = self.metrics.to_dict()
        metrics.update({
            "healthy": self._healthy,
            "running": self._running,
            "queue_size": self._queue.qsize() if self._queue else 0,
        })
        return metrics
        
    # Abstract methods that must be implemented by subclasses
    
    @abc.abstractmethod
    async def _initialize_connection(self) -> None:
        """Initialize connection to the remote service."""
        pass
        
    @abc.abstractmethod
    async def _cleanup_connection(self) -> None:
        """Cleanup connection resources."""
        pass
        
    @abc.abstractmethod
    async def _send_batch(self, messages: list[str]) -> int:
        """
        Send a batch of messages to the remote service.
        
        Args:
            messages: List of serialized log messages
            
        Returns:
            Total size of data sent in bytes
            
        Raises:
            Exception: If sending fails
        """
        pass
        
    @abc.abstractmethod
    async def _health_check(self) -> bool:
        """
        Perform a health check on the remote service.
        
        Returns:
            True if healthy, False otherwise
        """
        pass