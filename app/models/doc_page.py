import logging
from datetime import datetime

from peewee import (
    IntegerField,
    CharField,
    Model,
    InterfaceError,
    DatabaseError,
)
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

        if not title:
            return False

        if title == "error":
            now = int(datetime.now().timestamp() * 1000)
            title = str(now)

        # start db
        @retry(
            exceptions=(InterfaceError, DatabaseError, Exception),
            tries=4,
            delay=1,
            backoff=2,
            max_delay=100,
            logger=logger,
        )
        def insert():
            db.connect(reuse_if_open=True)
            cls.create(
                status="Draft",
                content=content_zh,
                title=title,
                summary=summary,
                slug=title,
            )

        # insert
        insert()

        return True
