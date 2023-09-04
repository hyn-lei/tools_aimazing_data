import logging

from peewee import IntegerField, CharField

from app.models.base_model import BaseModel
from app.providers.ai import Ai
from app.providers.deepl import Translator
from app.providers.database import db
from datetime import datetime

from config.config import settings


class Post(BaseModel):
    class Meta:
        database = db
        table_name = "posts"

    id = IntegerField(primary_key=True)
    status = CharField()
    content = CharField()
    content_zh = CharField()
    title = CharField()
    summary = CharField()
    slug = CharField()

    #
    translator = Translator()

    @classmethod
    def add(cls, content: str):
        content_zh = cls.translator.en_to_zh(content)
        logging.info(content_zh)
        now = int(datetime.now().timestamp() * 1000)
        summary = Ai().summarize2(content_zh)
        Post.create(
            status="Draft",
            content=content,
            content_zh=content_zh,
            title="title",
            summary=summary,
            slug="slug",
            created_at=now,
            updated_at=now,
        )
        # insert
