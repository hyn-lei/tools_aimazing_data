import json
import logging
import traceback
from datetime import datetime

from peewee import IntegerField, CharField

from app.models.base_model import BaseModel
from app.providers.ai import Ai
from app.providers.database import db_blog
from app.providers.deepl import Translator


class Post(BaseModel):
    class Meta:
        database = db_blog
        table_name = "posts"

    id = IntegerField(primary_key=True)
    status = CharField()
    content = CharField()
    content_zh = CharField()
    title = CharField()
    summary = CharField()
    slug = CharField()
    external_id = CharField()

    #
    translator = Translator()

    @classmethod
    def ai_handle(cls, content: str):
        if not content:
            return "", "", ""

        try:
            content_zh = Ai().en_to_zh(content)
        except Exception as e:
            error = traceback.format_exc()
            content_zh = "AI 翻译出错，" + error

        try:
            # logging.info(content_zh)
            s_data = Ai().summarize_in_sentences(content)
        except Exception as e:
            error = "AI 总结出错" + traceback.format_exc()
            logging.error(error)
            return "", error, content_zh

        try:
            j_data = json.loads(s_data)
            title = j_data.get("title")
            summary = j_data.get("summary")
        except Exception as e:
            error = "解析输出，AI 原始数据：" + s_data
            return "", error, content_zh

        return title, summary, content_zh

    @classmethod
    def add(cls, external_id: str, content: str):
        now = int(datetime.now().timestamp() * 1000)
        title, summary, content_zh = cls.ai_handle(content)

        Post.create(
            status="Draft",
            content=content,
            content_zh=content_zh,
            title=title,
            summary=summary,
            slug=title,
            created_at=now,
            updated_at=now,
            external_id=external_id,
        )
        # insert
