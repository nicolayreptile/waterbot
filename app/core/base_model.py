from tortoise import fields, Model


class PrimaryKeyModelMixin:
    id = fields.IntField(pk=True)


class TimestampModelMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class UserModelMixin:
    user_id = fields.IntField()

    @classmethod
    def filter_by_user(cls, user_id):
        return cls.filter(user_id=user_id).all()


class ChatModelMixin:
    chat_id = fields.IntField()


class BaseModel(Model, PrimaryKeyModelMixin, TimestampModelMixin):

    class Meta:
        abstract = True
