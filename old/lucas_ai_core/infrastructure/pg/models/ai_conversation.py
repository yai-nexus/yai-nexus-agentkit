from tortoise import fields
from tortoise.models import Model

from ..extra.extra_fields import BigIntStrField


class AIConversation(Model):
    """牛人推荐会话数据模型
    对应数据库表：ai_conversation
    """

    id = BigIntStrField(pk=True, description="ID，主键")
    title = fields.CharField(max_length=50, description="会话标题")
    context = fields.JSONField(description="职位信息")
    uni_identity_id = fields.CharField(
        max_length=128, null=False, default="", description="用户id"
    )
    identity_type = fields.CharField(
        max_length=50, null=True, default=None, description="用户身份类型"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True, description="创建时间", null=True
    )
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间", null=True)
    deleted_at = fields.DatetimeField(description="删除时间", default=None, null=True)
    uni_tenant_id = fields.CharField(
        max_length=128, null=True, default="", description="租户id"
    )
    avatar = fields.CharField(
        max_length=1024, description="头像", default=None, null=True
    )
    last_message = fields.TextField(description="最后一条消息", default=None)

    class Meta:
        table = "ai_conversation"
        table_description = "牛人推荐-会话"

    def __str__(self):
        return f"AIConversation(id={self.id}, title={self.title},avatar={self.avatar},last_message={self.last_message},updated_at={self.updated_at},context={self.context})"
