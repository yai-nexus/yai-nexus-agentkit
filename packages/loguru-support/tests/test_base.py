"""
Tests for base sink functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from yai_loguru_support.base import BaseSink, SinkConfig, SinkMetrics, SinkError


class MockSink(BaseSink):
    """Mock sink for testing base functionality."""
    
    def __init__(self, config: SinkConfig, fail_init=False, fail_send=False):
        self.fail_init = fail_init
        self.fail_send = fail_send
        self.sent_messages = []
        super().__init__(config)
        
    async def _initialize_connection(self):
        if self.fail_init:
            raise Exception("Mock init failure")
            
    async def _cleanup_connection(self):
        pass
        
    async def _send_batch(self, messages):
        if self.fail_send:
            raise Exception("Mock send failure")
        self.sent_messages.extend(messages)
        return sum(len(msg.encode('utf-8')) for msg in messages)
        
    async def _health_check(self):
        return not self.fail_send


class TestSinkConfig:
    """Test SinkConfig functionality."""
    
    def test_default_config(self):
        config = SinkConfig()
        assert config.level == "INFO"
        assert config.serialize is True
        assert config.max_workers == 4
        assert config.batch_size == 100
        
    def test_custom_config(self):
        config = SinkConfig(
            level="DEBUG",
            batch_size=500,
            max_retries=5
        )
        assert config.level == "DEBUG"
        assert config.batch_size == 500
        assert config.max_retries == 5


class TestSinkMetrics:
    """Test SinkMetrics functionality."""
    
    def test_initial_state(self):
        metrics = SinkMetrics()
        assert metrics.logs_sent == 0
        assert metrics.logs_failed == 0
        assert metrics.success_rate == 100.0
        
    def test_record_success(self):
        metrics = SinkMetrics()
        metrics.record_success(100)
        assert metrics.logs_sent == 1
        assert metrics.bytes_sent == 100
        assert metrics.success_rate == 100.0
        
    def test_record_failure(self):
        metrics = SinkMetrics()
        error = Exception("test error")
        metrics.record_failure(error)
        assert metrics.logs_failed == 1
        assert metrics.last_error == error
        assert metrics.success_rate == 0.0
        
    def test_success_rate_calculation(self):
        metrics = SinkMetrics()
        metrics.record_success()
        metrics.record_success()
        metrics.record_failure(Exception("test"))
        assert metrics.success_rate == (2/3) * 100
        
    def test_to_dict(self):
        metrics = SinkMetrics()
        metrics.record_success(50)
        data = metrics.to_dict()
        assert data["logs_sent"] == 1
        assert data["bytes_sent"] == 50
        assert "success_rate" in data
        assert "uptime" in data


@pytest.mark.asyncio
class TestBaseSink:
    """Test BaseSink functionality."""
    
    async def test_successful_initialization(self):
        config = SinkConfig()
        sink = MockSink(config)
        
        await sink.start()
        assert sink._running is True
        
        await sink.stop()
        assert sink._running is False
        
    async def test_failed_initialization(self):
        config = SinkConfig()
        sink = MockSink(config, fail_init=True)
        
        with pytest.raises(Exception):
            await sink.start()
            
    async def test_write_messages(self):
        config = SinkConfig(batch_size=2, flush_interval=0.1)
        sink = MockSink(config)
        
        await sink.start()
        
        # Write some messages
        sink.write("test message 1")
        sink.write("test message 2")
        
        # Wait for batch processing
        await asyncio.sleep(0.2)
        
        assert len(sink.sent_messages) == 2
        assert "test message 1" in sink.sent_messages
        assert "test message 2" in sink.sent_messages
        
        await sink.stop()
        
    async def test_metrics_collection(self):
        config = SinkConfig()
        sink = MockSink(config)
        
        await sink.start()
        
        # Write and process a message
        sink.write("test message")
        await asyncio.sleep(0.1)
        
        metrics = sink.get_metrics()
        assert "healthy" in metrics
        assert "running" in metrics
        assert "queue_size" in metrics
        
        await sink.stop()
        
    async def test_batch_processing(self):
        config = SinkConfig(batch_size=3, flush_interval=1.0)
        sink = MockSink(config)
        
        await sink.start()
        
        # Write messages to trigger batch processing
        for i in range(5):
            sink.write(f"message {i}")
            
        # Wait for batch processing
        await asyncio.sleep(0.2)
        
        # Should have processed at least one batch
        assert len(sink.sent_messages) >= 3
        
        await sink.stop()
        
    async def test_retry_mechanism(self):
        config = SinkConfig(max_retries=2, retry_delay=0.01)
        sink = MockSink(config, fail_send=True)
        
        await sink.start()
        
        # This should fail and be retried
        sink.write("test message")
        
        # Wait for retries to complete
        await asyncio.sleep(0.1)
        
        # Message should not be sent due to failures
        assert len(sink.sent_messages) == 0
        
        await sink.stop()
        
    async def test_graceful_shutdown(self):
        config = SinkConfig(batch_size=10, flush_interval=10.0)
        sink = MockSink(config)
        
        await sink.start()
        
        # Add some messages that haven't been flushed yet
        sink.write("message 1")
        sink.write("message 2")
        
        # Stop should flush remaining messages
        await sink.stop()
        
        # Messages should have been flushed during shutdown
        assert len(sink.sent_messages) == 2