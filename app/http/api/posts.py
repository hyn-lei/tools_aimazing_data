import json
import logging

from fastapi import APIRouter, Depends, Request

from app.http.deps import get_db
from app.models.data_card import DataCard
from app.models.post import Post
from app.models.user import User
from app.providers.github_data import git_hub_retriever
from app.services.auth import hashing
import requests

router = APIRouter(prefix="/posts")


def content_medium(id: str):
    url = f"https://medium2.p.rapidapi.com/article/{id}/markdown"

    headers = {
        "X-RapidAPI-Key": "07a05c759fmshd0cd5e0712bed8ap19e6a0jsn8c3d0b8d1654",
        "X-RapidAPI-Host": "medium2.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    return data.get("markdown")


@router.post("/", dependencies=[Depends(get_db)])
async def add(request: Request):
    data = await request.json()
    logging.info(data)
    medium_id = data.get("medium_id")
    if not medium_id:
        return {"error": "id invalid"}

    content = content_medium(medium_id)
    if not content:
        return {"error": "content empty"}

    # translate and insert
    Post.add(medium_id, content)
    return {"result": True}
