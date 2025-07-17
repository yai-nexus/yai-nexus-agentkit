"""
请求处理模块 - FastAPI 路由处理函数
"""
import time
import uuid
from ag_ui.core import RunAgentInput
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from yai_nexus_agentkit.adapter.models import Task


async def validate_and_create_task(request_data: RunAgentInput) -> Task:
    """
    提取的公共验证和 Task 创建逻辑

    Args:
        request_data: AG-UI 标准输入

    Returns:
        验证后的 Task 对象

    Raises:
        HTTPException: 当输入验证失败时
    """
    if not request_data.messages:
        raise HTTPException(
            status_code=400, detail="Request body must contain 'messages' array."
        )

    last_message = request_data.messages[-1]
    if not last_message.content.strip():
        raise HTTPException(
            status_code=400,
            detail="The last message must have non-empty 'content'.",
        )

    # 创建 Adapter 需要的 Task 对象
    return Task(
        id=request_data.run_id or f"run_{uuid.uuid4().hex}",
        query=last_message.content,
        thread_id=request_data.thread_id or f"thread_{uuid.uuid4().hex}",
    )


async def root():
    """根路径处理"""
    return {
        "message": "YAI Nexus FeKit Python Backend",
        "version": "0.1.0",
        "status": "running",
    }


async def health_check():
    """健康检查处理"""
    return {"status": "healthy", "timestamp": time.time()}


async def agui_agent(request_data: RunAgentInput, request: Request, agui_adapter):
    """
    为 HttpAgent 提供的 AG-UI 流式端点，使用官方 EventEncoder 确保格式兼容性
    """
    try:
        logger.info(
            "Received AG-UI agent request", 
            message_count=len(request_data.messages),
            run_id=request_data.run_id, 
            thread_id=request_data.thread_id
        )

        # 使用提取的公共验证逻辑
        task = await validate_and_create_task(request_data)

        logger.info(
            "Processing AG-UI streaming task", 
            task_id=task.id, 
            thread_id=task.thread_id
        )

        # 获取 accept header 用于 EventEncoder
        accept_header = request.headers.get("accept")
        logger.info("Request accept header", accept_header=accept_header)

        # 使用 AGUIAdapter 的统一官方流接口
        return StreamingResponse(
            agui_adapter.create_official_stream(task, accept_header),
            media_type="text/event-stream",
        )

    except HTTPException as http_exc:
        # 重新抛出 HTTP 异常，让 FastAPI 处理
        raise http_exc
    except Exception as e:
        # 对于其他所有异常，记录并返回一个标准的 500 错误
        logger.exception(
            "An unexpected error occurred in /agui endpoint",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )