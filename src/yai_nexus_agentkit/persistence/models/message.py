from tortoise import fields
from tortoise.models import Model


class AgentMessage(Model):
    """消息模型"""

    id = fields.UUIDField(pk=True)
    conversation: fields.ForeignKeyRelation["AgentConversation"] = (
        fields.ForeignKeyField(
            "models.AgentConversation",
            related_name="messages",
            on_delete=fields.CASCADE,
        )
    )
    role = fields.CharField(
        max_length=50, description="角色 (e.g., 'user', 'assistant')"
    )
    content = fields.TextField()
    metadata_ = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "agent_messages"
