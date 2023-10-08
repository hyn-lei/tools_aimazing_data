import json
import logging
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
    def add(cls, external_id: str, content: str):
        content_zh = Ai().en_to_zh(content)
        # logging.info(content_zh)
        now = int(datetime.now().timestamp() * 1000)
        s_data = Ai().summarize_in_sentences(content)
        logging.info(f"ai return, id:{external_id}, s_data:{s_data}")
        try:
            j_data = json.loads(s_data)
            title = j_data.get("title")
            summary = j_data.get("summary")
        except Exception as e:
            logging.error("解析 ai 总结数据出错，需要手工处理")
            title = external_id
            summary = "ai数据解析出错，需手工处理"

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
