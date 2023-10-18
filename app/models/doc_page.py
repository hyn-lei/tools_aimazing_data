import logging

from peewee import IntegerField, CharField, Model
from retry import retry

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
        logger = logging.getLogger(__name__)

        # start db
        @retry(tries=4, delay=1, backoff=2, max_delay=100, logger=logger)
        def insert():
            db.connect()
            cls.create(
                status="Draft",
                content=content_zh,
                title=title,
                summary=summary,
                slug=title,
            )

        # insert
        insert()
