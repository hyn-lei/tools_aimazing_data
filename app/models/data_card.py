from peewee import CharField, DateTimeField, IntegerField, BigIntegerField, Model
from playhouse.postgres_ext import JSONField

from app.providers.database import db


class DataCard(Model):
    class Meta:
        database = db
        table_name = 'data_cards'

    id = IntegerField(primary_key=True)
    status = CharField()
    sort = IntegerField()
    title = CharField()
    summary = CharField()
    featured_image = CharField()
    details = CharField()
    tags = JSONField()
    type = IntegerField()
    url = CharField()
    title_slug = CharField()
    author_avatar = CharField()
    license = CharField()
    stars = IntegerField()
    forks = IntegerField()
    watches = IntegerField()
    latest_version = CharField()
    latest_update = CharField()

    @classmethod
    def list_all(cls):
        query = DataCard.select().dicts()
        return list(query)
