from pydantic import BaseModel, field_validator


class SSEHandlerError(Exception):
    """SSE基础异常类"""

    def __init__(self, message: str, error_code: str = "SSE_HANDLER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class SSEConnectionClosedError(SSEHandlerError):
    """连接已关闭异常"""

    def __init__(self, message: str = "SSE connection is closed"):
        super().__init__(message, error_code="SSE_CONNECTION_CLOSED")


class SSEConfigurationError(SSEHandlerError):
    """配置错误异常"""

    def __init__(self, message: str):
        super().__init__(message, error_code="SSE_CONFIG_ERROR")


class SSEValidationError(SSEHandlerError):
    """验证错误异常"""

    def __init__(self, message: str):
        super().__init__(message, error_code="SSE_VALIDATION_ERROR")


class SSEConfig(BaseModel):
    """SSE配置验证模型"""

    retry_timeout: int = 30000
    heartbeat_interval: int = 15000

    @classmethod
    @field_validator("retry_timeout")
    def validate_retry_timeout(cls, v):
        if v <= 15000:
            raise SSEValidationError("Retry timeout must be at least 5 seconds")
        return v

    @classmethod
    @field_validator("heartbeat_interval")
    def validate_heartbeat_interval(cls, v):
        if v < 3000:
            raise SSEValidationError("Heartbeat interval must be at least 5 seconds")
        return v
