import logging

from peewee import IntegerField, CharField

from app.models.base_model import BaseModel
from app.providers.ai import Translator
from app.providers.database import db


from config.config import settings


class Post(BaseModel):
    class Meta:
        database = db
        table_name = "posts"

    id = IntegerField(primary_key=True)
    status = CharField()
    content = CharField()
    content_zh = CharField()

    #
    translator = Translator(settings.OPENAI_KEY)

    @classmethod
    def add(cls, content: str):
        content_zh = cls.translator.en_to_zh(content)
        logging.info(content_zh)

        # insert
