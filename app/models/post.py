from datetime import datetime

from peewee import IntegerField, CharField

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

        # start db
        get_db_blog()

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
