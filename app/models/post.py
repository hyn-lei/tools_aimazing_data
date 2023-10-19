import logging
from datetime import datetime

from peewee import IntegerField, CharField
from retry import retry

from app.http.deps import get_db_blog
from app.models.base_model import BaseModel
from app.providers.ai import ai_handle
from app.providers.database import db_blog


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

    @classmethod
    def add(cls, external_id: str, content: str):
        now = int(datetime.now().timestamp() * 1000)
        title, summary, content_zh = ai_handle(content)

        # start db，需要在 ai 接口调用之后执行，而不是在 api 接口层（ai 接口调用之前执行）
        logger = logging.getLogger(__name__)

        @retry(tries=4, delay=1, backoff=2, max_delay=100, logger=logger)
        def insert():
            db_blog.connect(reuse_if_open=True)
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
        insert()
