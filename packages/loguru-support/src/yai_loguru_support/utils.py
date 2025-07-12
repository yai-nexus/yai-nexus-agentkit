"""
Utility functions for graceful shutdown and signal handling.

This module provides helpers for integrating loguru sinks with various
application frameworks and deployment environments.
"""

import asyncio
import atexit
import signal
import threading
from typing import List, Callable, Optional, Any
from contextlib import contextmanager

from .base import BaseSink


class GracefulShutdown:
    """
    Manages graceful shutdown of multiple sinks.
    
    Provides signal handling, atexit integration, and framework-specific
    shutdown hooks for ensuring all logs are flushed before application exit.
    """
    
    def __init__(self):
        self._sinks: List[BaseSink] = []
        self._shutdown_callbacks: List[Callable] = []
        self._shutdown_lock = threading.Lock()
        self._shutdown_complete = False
        
    def register_sink(self, sink: BaseSink) -> None:
        """Register a sink for graceful shutdown."""
        with self._shutdown_lock:
            if sink not in self._sinks:
                self._sinks.append(sink)
                
    def unregister_sink(self, sink: BaseSink) -> None:
        """Unregister a sink from graceful shutdown."""
        with self._shutdown_lock:
            if sink in self._sinks:
                self._sinks.remove(sink)
                
    def register_callback(self, callback: Callable) -> None:
        """Register a custom shutdown callback."""
        with self._shutdown_lock:
            if callback not in self._shutdown_callbacks:
                self._shutdown_callbacks.append(callback)
                
    async def shutdown_all(self, timeout: float = 30.0) -> None:
        """
        Shutdown all registered sinks and run callbacks.
        
        Args:
            timeout: Maximum time to wait for shutdown completion
        """
        with self._shutdown_lock:
            if self._shutdown_complete:
                return
            self._shutdown_complete = True
            
        print("Gracefully shutting down loguru sinks...")
        
        # Run custom callbacks first
        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                print(f"Error in shutdown callback: {e}")
                
        # Shutdown all sinks
        shutdown_tasks = []
        for sink in self._sinks:
            try:
                task = asyncio.create_task(sink.stop())
                shutdown_tasks.append(task)
            except Exception as e:
                print(f"Error creating shutdown task for {sink}: {e}")
                
        if shutdown_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True),
                    timeout=timeout
                )
                print("All sinks shut down successfully")
            except asyncio.TimeoutError:
                print(f"Warning: Shutdown timed out after {timeout}s")
            except Exception as e:
                print(f"Error during sink shutdown: {e}")
                
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"Received signal {signum}, initiating graceful shutdown...")
            try:
                # Try to use existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule shutdown in the running loop
                    asyncio.create_task(self.shutdown_all())
                else:
                    # Run shutdown directly
                    loop.run_until_complete(self.shutdown_all())
            except RuntimeError:
                # No event loop, create a new one
                asyncio.run(self.shutdown_all())
            finally:
                # Exit gracefully
                exit(0)
                
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
    def setup_atexit(self) -> None:
        """Setup atexit handler for graceful shutdown."""
        def atexit_handler():
            if not self._shutdown_complete:
                try:
                    asyncio.run(self.shutdown_all())
                except Exception as e:
                    print(f"Error during atexit shutdown: {e}")
                    
        atexit.register(atexit_handler)
        
    def setup_fastapi(self, app) -> None:
        """
        Setup graceful shutdown for FastAPI applications.
        
        Args:
            app: FastAPI application instance
        """
        @app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown_all()
            
    def setup_flask(self, app) -> None:
        """
        Setup graceful shutdown for Flask applications.
        
        Args:
            app: Flask application instance
        """
        @app.teardown_appcontext
        def shutdown_handler(exception):
            # For Flask, we use atexit since teardown_appcontext
            # is called per request, not on app shutdown
            pass
            
        # Flask doesn't have built-in shutdown hooks,
        # so we rely on signal handlers and atexit
        self.setup_signal_handlers()
        self.setup_atexit()
        
    def setup_django(self) -> None:
        """Setup graceful shutdown for Django applications."""
        try:
            from django.core.signals import request_finished
            from django.dispatch import receiver
            
            # Django doesn't have built-in shutdown hooks for ASGI/WSGI apps,
            # so we use signal handlers and atexit
            self.setup_signal_handlers()
            self.setup_atexit()
            
        except ImportError:
            print("Django not available, using basic signal handlers")
            self.setup_signal_handlers()
            self.setup_atexit()


# Global shutdown manager instance
_shutdown_manager = GracefulShutdown()


def register_sink_for_shutdown(sink: BaseSink) -> None:
    """Register a sink for automatic graceful shutdown."""
    _shutdown_manager.register_sink(sink)


def setup_graceful_shutdown(
    app: Optional[Any] = None,
    framework: Optional[str] = None,
    enable_signals: bool = True,
    enable_atexit: bool = True
) -> GracefulShutdown:
    """
    Setup graceful shutdown for the application.
    
    Args:
        app: Application instance (FastAPI, Flask, etc.)
        framework: Framework name ('fastapi', 'flask', 'django')
        enable_signals: Whether to setup signal handlers
        enable_atexit: Whether to setup atexit handler
        
    Returns:
        GracefulShutdown instance for manual control
    """
    if enable_signals:
        _shutdown_manager.setup_signal_handlers()
        
    if enable_atexit:
        _shutdown_manager.setup_atexit()
        
    if app and framework:
        if framework.lower() == 'fastapi':
            _shutdown_manager.setup_fastapi(app)
        elif framework.lower() == 'flask':
            _shutdown_manager.setup_flask(app)
        elif framework.lower() == 'django':
            _shutdown_manager.setup_django()
        else:
            print(f"Unknown framework: {framework}")
            
    return _shutdown_manager


@contextmanager
def managed_sink(sink: BaseSink, auto_shutdown: bool = True):
    """
    Context manager for automatic sink lifecycle management.
    
    Args:
        sink: The sink to manage
        auto_shutdown: Whether to register for automatic shutdown
        
    Example:
        ```python
        with managed_sink(sls_sink) as sink:
            logger.add(sink, serialize=True, level="INFO")
            # Use logger normally
            logger.info("Hello!")
        # Sink is automatically stopped when exiting the context
        ```
    """
    try:
        if auto_shutdown:
            register_sink_for_shutdown(sink)
        yield sink
    finally:
        try:
            # Try async stop first
            if hasattr(sink, 'stop') and callable(getattr(sink, 'stop')):
                if asyncio.iscoroutinefunction(sink.stop):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(sink.stop())
                        else:
                            loop.run_until_complete(sink.stop())
                    except RuntimeError:
                        asyncio.run(sink.stop())
                else:
                    sink.stop()
        except Exception as e:
            print(f"Error stopping sink {sink}: {e}")


def create_production_setup(
    sinks: List[BaseSink],
    app: Optional[Any] = None,
    framework: Optional[str] = None
) -> None:
    """
    One-line setup for production environments.
    
    Args:
        sinks: List of sinks to manage
        app: Application instance
        framework: Framework name
        
    Example:
        ```python
        from yai_loguru_support.utils import create_production_setup
        from yai_loguru_support.sls import AliyunSlsSink
        
        sls_sink = AliyunSlsSink.from_env()
        create_production_setup([sls_sink], app=app, framework='fastapi')
        ```
    """
    # Register all sinks
    for sink in sinks:
        register_sink_for_shutdown(sink)
        
    # Setup graceful shutdown
    setup_graceful_shutdown(
        app=app,
        framework=framework,
        enable_signals=True,
        enable_atexit=True
    )
    
    print(f"Production setup complete with {len(sinks)} sinks")