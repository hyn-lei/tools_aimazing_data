import json

from peewee import CharField, DateTimeField, IntegerField, BigIntegerField, Model
from playhouse.postgres_ext import JSONField

from app.providers.ai import Ai
from app.providers.database import db
import logging

from config.config import settings


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

    #
    ai = Ai(settings.OPENAI_KEY)

    @classmethod
    def list_all(cls):
        query = DataCard.select().dicts()
        return list(query)

    @classmethod
    def update_or_create(cls, url, data, summarize: bool = False):
        name, full_name, avatar, summary, read_me_content, tags, star, fork, watch, license_, latest_update, \
            latest_version = data

        slug = full_name.replace("/", "_")
        model = DataCard.get_or_none(DataCard.title_slug == slug)
        if summarize:
            ai_json = json.loads(cls.ai.summarize(read_me_content))
            main_img = ai_json.get("main_image")
            sum_content = ai_json.get("summary")
            if sum_content:
                read_me_content = sum_content
        logging.info(f'update, url,{url}')
        # update
        if model:
            DataCard.update(summary=summary, tags=tags, license=license_,
                            stars=star, forks=fork, watches=watch, latest_update=latest_update,
                            latest_version=latest_version,
                            details=read_me_content
                            ).where(DataCard.title_slug == slug).execute()
            return

        # type=1开源工程
        logging.info(f'create, url, {url}')
        DataCard.create(status='draft', summary=summary,
                        tags=tags, url=url,
                        author_avatar=avatar,
                        license=license_,
                        stars=star, forks=fork, watches=watch, latest_update=latest_update,
                        latest_version=latest_version,
                        # 未知参数，或者需要处理的
                        details=read_me_content,
                        type=1, sort=0,
                        title=name, title_slug=slug,
                        featured_image=None
                        )
