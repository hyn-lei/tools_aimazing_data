from peewee import IntegerField, CharField, Model

from app.http.deps import get_db
from app.providers.ai import ai_handle
from app.providers.database import db


class DocPage(Model):
    class Meta:
        database = db
        table_name = "doc_pages"

    id = IntegerField(primary_key=True)
    status = CharField()
    content = CharField()
    title = CharField()
    summary = CharField()
    slug = CharField()

    @classmethod
    def add(cls, content: str):
        title, summary, content_zh = ai_handle(content)

        # start db
        get_db()
        cls.create(
            status="Draft",
            content=content_zh,
            title=title,
            summary=summary,
            slug=title,
        )
        # insert
