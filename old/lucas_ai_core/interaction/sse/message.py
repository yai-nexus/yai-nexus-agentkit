from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class MessageTypeEnum(Enum):
    """消息类型枚举"""

    CHAT = "chat"
    OPEN_FORM = "openForm"
    SUGGESTION = "suggestion"
    PROGRESS = "progress"


class SenderTypeEnum(Enum):
    """发送者类型枚举"""

    AI = "AI"


class BlockType(str, Enum):
    """块状结构类型"""

    TYPEWRITER = "typewriter"
    INDICATOR = "indicator"
    BUTTONS = "buttons"
    LOADING = "loading"


class SectionIdEnum(str, Enum):
    DESCRIPTION = "description"
    REQUIREMENTS = "requirements"


class SSEBaseMessage(BaseModel):
    """SSE基础消息模型"""

    messageId: str = Field(default="", description="消息id")
    conversationId: str = Field(default="", description="对话id")
    type: str = Field(..., description="消息类型")
    finish: bool = Field(default=False, description="是否结束")


class ContentBlock(BaseModel):
    """内容块模型"""

    blockId: str = Field(default="", description="块ID")
    blockType: str = Field(default=BlockType.TYPEWRITER.value, description="块类型")
    content: str = Field(default="", description="内容")
    action: str = Field(default="", description="action")


class Button(BaseModel):
    showText: str
    inputText: str
    action: str


class FunctionBlock(BaseModel):
    """功能块状结构"""

    blockId: str
    suggestionMessageId: str = Field(
        default="", description="suggestionMessageId消息id"
    )
    blockType: str = Field(default=BlockType.BUTTONS.value, description="块类型")
    action: str = Field(default="", description="action")
    buttons: List[Button]


class LoadingBlock(BaseModel):
    """加载块状结构"""

    blockId: str
    suggestionMessageId: str = Field(default="", description="suggestionMessageId")
    blockType: str = Field(default=BlockType.LOADING.value, description="块类型")
    hidden: bool
    action: str = Field(default="", description="action")
    buttons: Optional[List[Button]] = Field(default=None, description="buttons")


class BlockMessage(SSEBaseMessage):
    """块消息模型"""

    type: str = MessageTypeEnum.CHAT.value
    sender: str = SenderTypeEnum.AI.value
    blocks: List[Union[ContentBlock, FunctionBlock, LoadingBlock]] = Field(
        default_factory=list, description="内容块列表"
    )


class ProgressMessage(SSEBaseMessage):
    """进度消息模型"""

    type: str = MessageTypeEnum.PROGRESS.value
    stage: str = Field(..., description="stage")
    message: str = Field(..., description="message")
    progress: float = Field(..., description="progress")
    details: Optional[Dict[str, Any]] = None


class OptimizationSection(BaseModel):
    sectionId: SectionIdEnum = Field(..., description="Section ID")
    index: Optional[int] = Field(0, description="Index of section")
    field: SectionIdEnum = Field(..., description="Field name, same to sectionId field")
    before: str = Field(..., description="Content before optimization")
    optimized: str = Field(..., description="Content after optimization")


class ContentMessage(SSEBaseMessage):
    """内容优化模型"""

    type: str = MessageTypeEnum.SUGGESTION.value
    sender: str = SenderTypeEnum.AI.value
    sections: List[Union[Dict[str, Any], OptimizationSection]]
