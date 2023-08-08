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

        kw = {"summary": summary, "tags": tags, "license": license_, "author_avatar": avatar,
              "stars": star, "forks": fork, "watches": watch, "latest_update": latest_update,
              "latest_version": latest_version}

        slug = full_name.replace("/", "_")
        model = DataCard.get_or_none(DataCard.title_slug == slug)
        if summarize:
            sum_content = cls.ai.summarize(read_me_content)
            logging.info(f'ai working: {sum_content}')
            if sum_content:
                kw['details'] = sum_content
            else:
                kw['details'] = read_me_content

        logging.info(f'update, url,{url}')
        # update

        if model:
            DataCard.update(**kw).where(DataCard.title_slug == slug).execute()
            return

        # type=1开源工程
        logging.info(f'create, url, {url}')
        kw["status"] = 'draft'
        kw['url'] = url
        kw['type'] = 1
        kw['sort'] = 0
        kw['title'] = name
        kw['title_slug'] = slug
        kw['featured_image'] = None

        DataCard.create(**kw)
