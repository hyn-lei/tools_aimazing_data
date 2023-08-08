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
    if not data:
        return

    DataCard.update_or_create(url, data, True)


@router.get("/{id_}", dependencies=[Depends(get_db)])
async def show(id_: str):
    data = DataCard.get_by_id(id_)
    return data.__data__
