from tortoise import fields
from tortoise.models import Model

class AgentConversation(Model):
    """会话模型"""
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=255, null=True)
    metadata_ = fields.JSONField(null=True, description="元数据")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "agent_conversations"