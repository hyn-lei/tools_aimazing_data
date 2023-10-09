from peewee import DateTimeField, Model, SQL, BigIntegerField

from app.providers.database import db


class BaseModel(Model):
    created_at = BigIntegerField()
    updated_at = BigIntegerField()

    class Meta:
        database = db


class BaseModelWithSoftDelete(BaseModel):
    deleted_at = DateTimeField(null=True)

    @classmethod
    def undelete(cls):
        return cls.select().where(SQL("deleted_at is NULL"))
