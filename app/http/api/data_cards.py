import json
import logging

from fastapi import APIRouter, Depends, Request

from app.http.deps import get_db
from app.models.data_card import DataCard
from app.models.user import User
from app.providers.github_data import git_hub_retriever
from app.services.auth import hashing

router = APIRouter(
    prefix="/data_cards"
)


@router.get("/")
async def index():
    data = DataCard.select().dicts()
    return list(data)


@router.post("/", dependencies=[Depends(get_db)])
async def db_test(request: Request):
    j_data = await request.json()
    logging.info(f'post:{j_data}')

    url = j_data.get('url')
    if not url:
        return None

    add_one(url=url)
    return {'result': 'ok'}


def add_one(url: str = None):
    logging.info(f"save data from url:{url}")

    data = git_hub_retriever(github_url=url)
    name, full_name, avatar, summary, read_me_content, tags, star, fork, watch, license_, latest_update, \
        latest_version = data

    # type=1开源工程
    DataCard.create(status='draft', summary=summary,
                    tags=tags, url=url,
                    author_avatar=avatar,
                    license=license_,
                    stars=star, forks=fork, watches=watch, latest_update=latest_update, latest_version=latest_version,
                    # 未知参数，或者需要处理的
                    details=read_me_content,
                    type=1, sort=0,
                    title=name, title_slug=full_name.replace("/", "_"),
                    featured_image=None
                    )


@router.get("/{id_}", dependencies=[Depends(get_db)])
async def show(id_: str):
    data = DataCard.get_by_id(id_)
    return data.__data__
