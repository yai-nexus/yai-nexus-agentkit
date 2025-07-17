"""
中间件模块 - 处理请求日志和跨域
"""
import time
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


def setup_middleware(app):
    """设置应用中间件"""
    
    # 简单的请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            logger.info(
                f"Response: {response.status_code} ({duration:.2f}s)",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {e}",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration * 1000, 2)
            )
            raise

    # Enable CORS for the frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )